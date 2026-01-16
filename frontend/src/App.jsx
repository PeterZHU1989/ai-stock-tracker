from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import yfinance as yf
import threading
import time
import xml.etree.ElementTree as ET
from datetime import datetime
import random

app = FastAPI()

# 版本标识，用于确认部署是否生效
APP_VERSION = "2026.01.15.V2" 

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. 股票配置池 (已确认：港股已移除联想/小米，新增剑桥/英诺/阿里/快手等) ---
STOCKS_CONFIG = [
    # ==================== 🇺🇸 美股 (US) ====================
    {"id": "NVDA", "sina_code": "gb_nvda", "ticker": "NVDA", "name": "英伟达", "market": "US", "sector": "hardware", "subSector": "GPU 芯片", "query": "NVIDIA stock news"},
    {"id": "AMD", "sina_code": "gb_amd", "ticker": "AMD", "name": "超微半导体", "market": "US", "sector": "hardware", "subSector": "GPU 芯片", "query": "AMD stock news"},
    {"id": "AVGO", "sina_code": "gb_avgo", "ticker": "AVGO", "name": "博通", "market": "US", "sector": "hardware", "subSector": "网络/ASIC", "query": "Broadcom stock news"},
    {"id": "MU", "sina_code": "gb_mu", "ticker": "MU", "name": "镁光科技", "market": "US", "sector": "hardware", "subSector": "HBM 存储", "query": "Micron Technology news"},
    {"id": "TSM_US", "sina_code": "gb_tsm", "ticker": "TSM", "name": "台积电(ADR)", "market": "US", "sector": "hardware", "subSector": "晶圆代工", "query": "TSMC stock news"},
    {"id": "SMCI", "sina_code": "gb_smci", "ticker": "SMCI", "name": "超微电脑", "market": "US", "sector": "hardware", "subSector": "AI 服务器", "query": "Super Micro news"},
    {"id": "MRVL", "sina_code": "gb_mrvl", "ticker": "MRVL", "name": "Marvell", "market": "US", "sector": "hardware", "subSector": "光/电芯片", "query": "Marvell Technology news"},
    {"id": "APH", "sina_code": "gb_aph", "ticker": "APH", "name": "安费诺", "market": "US", "sector": "hardware", "subSector": "连接器", "query": "Amphenol stock news"},
    {"id": "TEL", "sina_code": "gb_tel", "ticker": "TEL", "name": "泰科电子", "market": "US", "sector": "hardware", "subSector": "连接器", "query": "TE Connectivity news"},
    {"id": "COHR", "sina_code": "gb_cohr", "ticker": "COHR", "name": "Coherent", "market": "US", "sector": "hardware", "subSector": "光电子", "query": "Coherent stock news"},
    {"id": "TSLA", "sina_code": "gb_tsla", "ticker": "TSLA", "name": "特斯拉", "market": "US", "sector": "hardware", "subSector": "机器人/Dojo", "query": "Tesla AI news"},
    {"id": "MSFT", "sina_code": "gb_msft", "ticker": "MSFT", "name": "微软", "market": "US", "sector": "application", "subSector": "云/模型", "query": "Microsoft AI news"},
    {"id": "GOOGL", "sina_code": "gb_googl", "ticker": "GOOGL", "name": "谷歌", "market": "US", "sector": "application", "subSector": "搜索/模型", "query": "Google Gemini news"},
    {"id": "META", "sina_code": "gb_meta", "ticker": "META", "name": "Meta", "market": "US", "sector": "application", "subSector": "社交/模型", "query": "Meta Llama news"},
    {"id": "APP", "sina_code": "gb_app", "ticker": "APP", "name": "AppLovin", "market": "US", "sector": "application", "subSector": "AI 营销", "query": "AppLovin stock news"},
    {"id": "CRM", "sina_code": "gb_crm", "ticker": "CRM", "name": "Salesforce", "market": "US", "sector": "application", "subSector": "企业 AI", "query": "Salesforce AI news"},
    {"id": "PLTR", "sina_code": "gb_pltr", "ticker": "PLTR", "name": "Palantir", "market": "US", "sector": "application", "subSector": "数据分析", "query": "Palantir stock news"},

    # ==================== 🇨🇳 A股 (CN) ====================
    {"id": "601138", "sina_code": "sh601138", "ticker": "601138.SS", "name": "工业富联", "market": "CN", "sector": "hardware", "subSector": "AI 服务器", "query": "工业富联 新闻"},
    {"id": "300308", "sina_code": "sz300308", "ticker": "300308.SZ", "name": "中际旭创", "market": "CN", "sector": "hardware", "subSector": "光模块", "query": "中际旭创 新闻"},
    {"id": "688041", "sina_code": "sh688041", "ticker": "688041.SS", "name": "海光信息", "market": "CN", "sector": "hardware", "subSector": "AI 芯片", "query": "海光信息 新闻"},
    {"id": "688256", "sina_code": "sh688256", "ticker": "688256.SS", "name": "寒武纪", "market": "CN", "sector": "hardware", "subSector": "AI 芯片", "query": "寒武纪 新闻"},
    {"id": "300394", "sina_code": "sz300394", "ticker": "300394.SZ", "name": "天孚通信", "market": "CN", "sector": "hardware", "subSector": "光器件", "query": "天孚通信 新闻"},
    {"id": "688498", "sina_code": "sh688498", "ticker": "688498.SS", "name": "源杰科技", "market": "CN", "sector": "hardware", "subSector": "光芯片", "query": "源杰科技 新闻"},
    {"id": "002463", "sina_code": "sz002463", "ticker": "002463.SZ", "name": "沪电股份", "market": "CN", "sector": "hardware", "subSector": "PCB", "query": "沪电股份 新闻"},
    {"id": "300476", "sina_code": "sz300476", "ticker": "300476.SZ", "name": "胜宏科技", "market": "CN", "sector": "hardware", "subSector": "PCB", "query": "胜宏科技 新闻"},
    {"id": "002938", "sina_code": "sz002938", "ticker": "002938.SZ", "name": "鹏鼎控股", "market": "CN", "sector": "hardware", "subSector": "PCB", "query": "鹏鼎控股 新闻"},
    {"id": "002837", "sina_code": "sz002837", "ticker": "002837.SZ", "name": "英维克", "market": "CN", "sector": "hardware", "subSector": "液冷温控", "query": "英维克 新闻"},
    {"id": "688668", "sina_code": "sh688668", "ticker": "688668.SS", "name": "鼎通科技", "market": "CN", "sector": "hardware", "subSector": "连接器", "query": "鼎通科技 新闻"},
    {"id": "002851", "sina_code": "sz002851", "ticker": "002851.SZ", "name": "麦格米特", "market": "CN", "sector": "hardware", "subSector": "AI 电源", "query": "麦格米特 新闻"},
    {"id": "688111", "sina_code": "sh688111", "ticker": "688111.SS", "name": "金山办公", "market": "CN", "sector": "application", "subSector": "办公 AI", "query": "金山办公 新闻"},
    {"id": "002230", "sina_code": "sz002230", "ticker": "002230.SZ", "name": "科大讯飞", "market": "CN", "sector": "application", "subSector": "语音/模型", "query": "科大讯飞 新闻"},
    {"id": "600588", "sina_code": "sh600588", "ticker": "600588.SS", "name": "用友网络", "market": "CN", "sector": "application", "subSector": "企业 AI", "query": "用友网络 新闻"},

    # ==================== 🇭🇰 港股 (HK) ====================
    # --- 硬件 ---
    {"id": "0981", "sina_code": "rt_hk00981", "ticker": "0981.HK", "name": "中芯国际", "market": "HK", "sector": "hardware", "subSector": "晶圆代工", "query": "中芯国际 新闻"},
    {"id": "1888", "sina_code": "rt_hk01888", "ticker": "1888.HK", "name": "建滔积层板", "market": "HK", "sector": "hardware", "subSector": "CCL 覆铜板", "query": "建滔积层板 新闻"},
    {"id": "06166", "sina_code": "rt_hk06166", "ticker": "06166.HK", "name": "剑桥科技", "market": "HK", "sector": "hardware", "subSector": "光模块(H)", "query": "剑桥科技 港股 新闻"},
    {"id": "02577", "sina_code": "rt_hk02577", "ticker": "02577.HK", "name": "英诺赛科", "market": "HK", "sector": "hardware", "subSector": "氮化镓", "query": "英诺赛科 新闻"},
    
    # --- 软件/应用 ---
    {"id": "0700", "sina_code": "rt_hk00700", "ticker": "0700.HK", "name": "腾讯控股", "market": "HK", "sector": "application", "subSector": "社交/游戏", "query": "腾讯 混元大模型 新闻"},
    {"id": "09988", "sina_code": "rt_hk09988", "ticker": "9988.HK", "name": "阿里巴巴", "market": "HK", "sector": "application", "subSector": "云/电商", "query": "阿里巴巴 阿里云 新闻"},
    {"id": "01024", "sina_code": "rt_hk01024", "ticker": "1024.HK", "name": "快手", "market": "HK", "sector": "application", "subSector": "视频 AI", "query": "快手 可灵AI 新闻"},
    {"id": "09888", "sina_code": "rt_hk09888", "ticker": "9888.HK", "name": "百度集团", "market": "HK", "sector": "application", "subSector": "搜索/驾驶", "query": "百度 文心一言 新闻"},
    {"id": "03888", "sina_code": "rt_hk03888", "ticker": "3888.HK", "name": "金山软件", "market": "HK", "sector": "application", "subSector": "软件/游戏", "query": "金山软件 新闻"},
    {"id": "01357", "sina_code": "rt_hk01357", "ticker": "1357.HK", "name": "美图公司", "market": "HK", "sector": "application", "subSector": "视觉 AI", "query": "美图公司 AI新闻"},
    {"id": "09660", "sina_code": "rt_hk09660", "ticker": "9660.HK", "name": "地平线", "market": "HK", "sector": "application", "subSector": "智驾芯片", "query": "地平线 机器人 新闻"},
    {"id": "02513", "sina_code": "rt_hk02513", "ticker": "02513.HK", "name": "智谱 AI", "market": "HK", "sector": "application", "subSector": "大模型", "query": "智谱AI 新闻"},
    {"id": "00020", "sina_code": "rt_hk00020", "ticker": "0020.HK", "name": "商汤", "market": "HK", "sector": "application", "subSector": "视觉 AI", "query": "商汤科技 新闻"},

    # ==================== 🇹🇼 台股 (TW) ====================
    {"id": "2330", "sina_code": None, "ticker": "2330.TW", "name": "台积电", "market": "TW", "sector": "hardware", "subSector": "晶圆代工", "query": "台积电 财报 新闻"},
    {"id": "2317", "sina_code": None, "ticker": "2317.TW", "name": "鸿海", "market": "TW", "sector": "hardware", "subSector": "代工/服务器", "query": "鸿海精密 鸿海AI 新闻"},
    {"id": "2454", "sina_code": None, "ticker": "2454.TW", "name": "联发科", "market": "TW", "sector": "hardware", "subSector": "IC 设计", "query": "联发科 天玑 新闻"},
    {"id": "2382", "sina_code": None, "ticker": "2382.TW", "name": "广达", "market": "TW", "sector": "hardware", "subSector": "AI 服务器", "query": "广达电脑 新闻"},
    {"id": "6669", "sina_code": None, "ticker": "6669.TW", "name": "纬颖", "market": "TW", "sector": "hardware", "subSector": "云端服务器", "query": "纬颖科技 新闻"},
]

# --- 2. 新闻抓取模块 ---
NEWS_CACHE = {}

def fetch_google_news_rss(query, stock_id):
    if any(keyword in query for keyword in ["新闻", "港股", "财报"]):
        rss_url = f"https://news.google.com/rss/search?q={query}&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"
    else:
        rss_url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = requests.get(rss_url, headers=headers, timeout=8)
        if resp.status_code == 200:
            root = ET.fromstring(resp.content)
            item = root.find(".//item")
            if item is not None:
                title = item.find("title").text
                link = item.find("link").text
                clean_title = title.split(" - ")[0]
                return {"title": clean_title, "link": link}
    except Exception as e:
        print(f"[{stock_id}] News Fetch Error: {e}")
    return None

def background_news_updater():
    print(f">>> 后台新闻抓取线程启动 (版本: {APP_VERSION})...")
    while True:
        stocks = list(STOCKS_CONFIG)
        random.shuffle(stocks)
        for stock in stocks:
            news = fetch_google_news_rss(stock["query"], stock["id"])
            if news:
                NEWS_CACHE[stock["id"]] = news
            time.sleep(3) 
        print(f"[{datetime.now().strftime('%H:%M')}] 全量新闻缓存已刷新，休眠 20 分钟...")
        time.sleep(1200)

t = threading.Thread(target=background_news_updater, daemon=True)
t.start()

# --- 3. 行情数据获取 ---
def fetch_sina_batch():
    sina_stocks = [s for s in STOCKS_CONFIG if s['sina_code']]
    codes = ",".join([s['sina_code'] for s in sina_stocks])
    url = f"http://hq.sinajs.cn/list={codes}"
    headers = {"Referer": "http://finance.sina.com.cn/"}
    results = {}
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        content = resp.content.decode('gbk')
        for line in content.splitlines():
            if not line or "=" not in line: continue
            try:
                code_part, data_part = line.split('=')
                code = code_part.split('_str_')[-1]
                data = data_part.strip('";').split(',')
                if len(data) < 5: continue
                price, change_p, change_a = 0.0, 0.0, 0.0
                if code.startswith('gb_'): 
                    price, change_p, change_a = float(data[1]), float(data[2]), float(data[4])
                elif code.startswith('rt_hk'): 
                    price, prev = float(data[6]), float(data[3])
                    change_a = price - prev
                    change_p = (change_a / prev * 100) if prev else 0
                else: 
                    price, prev = float(data[3]), float(data[2])
                    change_a = price - prev
                    change_p = (change_a / prev * 100) if prev else 0
                results[code] = {"currentPrice": round(price, 2), "changePercent": round(change_p, 2), "changeAmount": round(change_a, 2)}
            except: continue
    except: pass
    return results

def fetch_yahoo_tw():
    tw_stocks = [s for s in STOCKS_CONFIG if not s['sina_code']]
    tickers = [s['ticker'] for s in tw_stocks]
    results = {}
    try:
        data = yf.download(tickers, period="2d", interval="1d", group_by='ticker', threads=True, progress=False)
        for stock in tw_stocks:
            ticker = stock['ticker']
            try:
                df = data if len(tickers) == 1 else data[ticker]
                if df.empty: continue
                price = float(df['Close'].iloc[-1])
                prev = float(df['Close'].iloc[-2]) if len(df) > 1 else price
                results[ticker] = {"currentPrice": round(price, 2), "changePercent": round(((price-prev)/prev)*100, 2), "changeAmount": round(price-prev, 2)}
            except: pass
    except: pass
    return results

@app.get("/")
def read_root():
    return {
        "status": "online", 
        "version": APP_VERSION, 
        "stocks_count": len(STOCKS_CONFIG),
        "cached_news": len(NEWS_CACHE)
    }

@app.get("/api/stocks")
def get_stocks():
    sina_data, yahoo_data = {}, {}
    def run_s(): nonlocal sina_data; sina_data = fetch_sina_batch()
    def run_y(): nonlocal yahoo_data; yahoo_data = fetch_yahoo_tw()
    t1 = threading.Thread(target=run_s); t2 = threading.Thread(target=run_y)
    t1.start(); t2.start(); t1.join(); t2.join()
    final_list = []
    for stock in STOCKS_CONFIG:
        item = {**stock}
        m_data = sina_data.get(stock['sina_code']) if stock['sina_code'] else yahoo_data.get(stock['ticker'])
        if m_data: item.update(m_data)
        else: item.update({"currentPrice": "-", "changePercent": 0, "changeAmount": 0, "error": True})
        item["news"] = NEWS_CACHE.get(stock["id"], {"title": "正在同步最新热点...", "link": "#"})
        final_list.append(item)
    return final_list