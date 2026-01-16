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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. 股票配置 (移除硬编码的热点，只保留基础信息) ---
STOCKS_CONFIG = [
    # === 美股 ===
    {"id": "NVDA", "sina_code": "gb_nvda", "ticker": "NVDA", "name": "英伟达", "market": "US", "sector": "hardware", "subSector": "GPU 芯片", "query": "NVIDIA stock news"},
    {"id": "AMD", "sina_code": "gb_amd", "ticker": "AMD", "name": "超微半导体", "market": "US", "sector": "hardware", "subSector": "GPU 芯片", "query": "AMD stock news"},
    {"id": "AVGO", "sina_code": "gb_avgo", "ticker": "AVGO", "name": "博通", "market": "US", "sector": "hardware", "subSector": "网络/ASIC", "query": "Broadcom stock news"},
    {"id": "MU", "sina_code": "gb_mu", "ticker": "MU", "name": "镁光科技", "market": "US", "sector": "hardware", "subSector": "HBM 存储", "query": "Micron Technology stock news"},
    {"id": "TSM_US", "sina_code": "gb_tsm", "ticker": "TSM", "name": "台积电(ADR)", "market": "US", "sector": "hardware", "subSector": "晶圆代工", "query": "TSMC stock news"},
    {"id": "SMCI", "sina_code": "gb_smci", "ticker": "SMCI", "name": "超微电脑", "market": "US", "sector": "hardware", "subSector": "AI 服务器", "query": "Super Micro Computer stock news"},
    {"id": "MRVL", "sina_code": "gb_mrvl", "ticker": "MRVL", "name": "Marvell", "market": "US", "sector": "hardware", "subSector": "光/电芯片", "query": "Marvell Technology news"},
    {"id": "TSLA", "sina_code": "gb_tsla", "ticker": "TSLA", "name": "特斯拉", "market": "US", "sector": "hardware", "subSector": "机器人/Dojo", "query": "Tesla stock news"},
    {"id": "MSFT", "sina_code": "gb_msft", "ticker": "MSFT", "name": "微软", "market": "US", "sector": "application", "subSector": "云/模型", "query": "Microsoft AI news"},
    {"id": "GOOGL", "sina_code": "gb_googl", "ticker": "GOOGL", "name": "谷歌", "market": "US", "sector": "application", "subSector": "搜索/模型", "query": "Google Alphabet AI news"},
    {"id": "META", "sina_code": "gb_meta", "ticker": "META", "name": "Meta", "market": "US", "sector": "application", "subSector": "社交/模型", "query": "Meta Platforms AI news"},
    {"id": "APP", "sina_code": "gb_app", "ticker": "APP", "name": "AppLovin", "market": "US", "sector": "application", "subSector": "AI 营销", "query": "AppLovin stock news"},
    {"id": "PLTR", "sina_code": "gb_pltr", "ticker": "PLTR", "name": "Palantir", "market": "US", "sector": "application", "subSector": "数据分析", "query": "Palantir Technologies news"},

    # === A股 (使用中文查询) ===
    {"id": "601138", "sina_code": "sh601138", "ticker": "601138.SS", "name": "工业富联", "market": "CN", "sector": "hardware", "subSector": "AI 服务器", "query": "工业富联 新闻"},
    {"id": "300308", "sina_code": "sz300308", "ticker": "300308.SZ", "name": "中际旭创", "market": "CN", "sector": "hardware", "subSector": "光模块", "query": "中际旭创 新闻"},
    {"id": "688041", "sina_code": "sh688041", "ticker": "688041.SS", "name": "海光信息", "market": "CN", "sector": "hardware", "subSector": "AI 芯片", "query": "海光信息 新闻"},
    {"id": "688256", "sina_code": "sh688256", "ticker": "688256.SS", "name": "寒武纪", "market": "CN", "sector": "hardware", "subSector": "AI 芯片", "query": "寒武纪 新闻"},
    {"id": "300394", "sina_code": "sz300394", "ticker": "300394.SZ", "name": "天孚通信", "market": "CN", "sector": "hardware", "subSector": "光器件", "query": "天孚通信 新闻"},
    {"id": "002463", "sina_code": "sz002463", "ticker": "002463.SZ", "name": "沪电股份", "market": "CN", "sector": "hardware", "subSector": "PCB", "query": "沪电股份 新闻"},
    {"id": "002230", "sina_code": "sz002230", "ticker": "002230.SZ", "name": "科大讯飞", "market": "CN", "sector": "application", "subSector": "语音/模型", "query": "科大讯飞 新闻"},
    {"id": "688111", "sina_code": "sh688111", "ticker": "688111.SS", "name": "金山办公", "market": "CN", "sector": "application", "subSector": "办公 AI", "query": "金山办公 新闻"},

    # === 港股 ===
    {"id": "0981", "sina_code": "rt_hk00981", "ticker": "0981.HK", "name": "中芯国际", "market": "HK", "sector": "hardware", "subSector": "晶圆代工", "query": "中芯国际 港股 新闻"},
    {"id": "0700", "sina_code": "rt_hk00700", "ticker": "0700.HK", "name": "腾讯控股", "market": "HK", "sector": "application", "subSector": "社交/游戏", "query": "腾讯控股 新闻"},
    {"id": "09988", "sina_code": "rt_hk09988", "ticker": "9988.HK", "name": "阿里巴巴", "market": "HK", "sector": "application", "subSector": "云/电商", "query": "阿里巴巴 港股 新闻"},
    {"id": "09888", "sina_code": "rt_hk09888", "ticker": "9888.HK", "name": "百度集团", "market": "HK", "sector": "application", "subSector": "搜索/驾驶", "query": "百度集团 港股 新闻"},
    {"id": "02513", "sina_code": "rt_hk02513", "ticker": "02513.HK", "name": "智谱 AI", "market": "HK", "sector": "application", "subSector": "大模型", "query": "智谱AI 新闻"},
    {"id": "00020", "sina_code": "rt_hk00020", "ticker": "0020.HK", "name": "商汤", "market": "HK", "sector": "application", "subSector": "视觉 AI", "query": "商汤科技 新闻"},
    
    # === 台股 ===
    {"id": "2330", "sina_code": None, "ticker": "2330.TW", "name": "台积电", "market": "TW", "sector": "hardware", "subSector": "晶圆代工", "query": "台积电 财报 新闻"},
    {"id": "2317", "sina_code": None, "ticker": "2317.TW", "name": "鸿海", "market": "TW", "sector": "hardware", "subSector": "代工/服务器", "query": "鸿海精密 新闻"},
    {"id": "2454", "sina_code": None, "ticker": "2454.TW", "name": "联发科", "market": "TW", "sector": "hardware", "subSector": "IC 设计", "query": "联发科 新闻"},
    {"id": "2382", "sina_code": None, "ticker": "2382.TW", "name": "广达", "market": "TW", "sector": "hardware", "subSector": "AI 服务器", "query": "广达电脑 新闻"},
]

# --- 2. 新闻抓取模块 (Google RSS) ---
NEWS_CACHE = {}  # 内存缓存

def fetch_google_news_rss(query):
    """抓取 Google News RSS 并解析第一条新闻"""
    # 针对不同语言设置不同的 RSS 地址
    if "新闻" in query:
        rss_url = f"https://news.google.com/rss/search?q={query}&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"
    else:
        rss_url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
        
    try:
        resp = requests.get(rss_url, timeout=5)
        if resp.status_code == 200:
            root = ET.fromstring(resp.content)
            # 获取第一条新闻 (<item>)
            item = root.find(".//item")
            if item is not None:
                title = item.find("title").text
                link = item.find("link").text
                pubDate = item.find("pubDate").text
                # 清理标题中的来源后缀 (例如 " - Yahoo Finance")
                clean_title = title.split(" - ")[0]
                return {"title": clean_title, "link": link, "date": pubDate}
    except Exception as e:
        print(f"News Fetch Error ({query}): {e}")
    
    return None

def background_news_updater():
    """后台线程：循环更新新闻"""
    print("启动后台新闻抓取线程...")
    while True:
        for stock in STOCKS_CONFIG:
            news = fetch_google_news_rss(stock["query"])
            if news:
                NEWS_CACHE[stock["id"]] = news
            # 礼貌抓取，避免被封 IP，每只股票间隔 2 秒
            time.sleep(2) 
        
        print(f"[{datetime.now().strftime('%H:%M')}] 所有股票新闻更新完毕，休眠 15 分钟...")
        time.sleep(900) # 每15分钟轮询一轮

# 启动后台线程
t = threading.Thread(target=background_news_updater, daemon=True)
t.start()

# --- 3. 行情数据获取 (混合引擎) ---
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
            if not line: continue
            try:
                code_part, data_part = line.split('=')
                code = code_part.split('_str_')[-1]
                data = data_part.strip('";').split(',')
                if len(data) < 5: continue
                
                price = 0.0
                prev_close = 0.0
                if code.startswith('gb_'): 
                    price = float(data[1])
                    change_percent = float(data[2])
                    change_amount = float(data[4])
                elif code.startswith('rt_hk'): 
                    price = float(data[6])
                    prev_close = float(data[3])
                    change_amount = price - prev_close
                    change_percent = (change_amount / prev_close) * 100 if prev_close else 0
                else: 
                    price = float(data[3])
                    prev_close = float(data[2])
                    change_amount = price - prev_close
                    change_percent = (change_amount / prev_close) * 100 if prev_close else 0
                
                results[code] = {
                    "currentPrice": round(price, 2),
                    "changePercent": round(change_percent, 2),
                    "changeAmount": round(change_amount, 2)
                }
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
                if len(tickers) == 1: df = data
                else: df = data[ticker]
                if df.empty: continue
                price = float(df['Close'].iloc[-1])
                prev = float(df['Close'].iloc[-2]) if len(df) > 1 else price
                results[ticker] = {
                    "currentPrice": round(price, 2),
                    "changePercent": round(((price - prev)/prev)*100, 2),
                    "changeAmount": round(price - prev, 2)
                }
            except: pass
    except: pass
    return results

@app.get("/")
def read_root():
    return {"status": "online", "news_cached_count": len(NEWS_CACHE)}

@app.get("/api/stocks")
def get_stocks():
    # 并行抓取价格
    sina_data = {}
    yahoo_data = {}
    
    def run_sina(): nonlocal sina_data; sina_data = fetch_sina_batch()
    def run_yahoo(): nonlocal yahoo_data; yahoo_data = fetch_yahoo_tw()
    
    t1 = threading.Thread(target=run_sina); t2 = threading.Thread(target=run_yahoo)
    t1.start(); t2.start(); t1.join(); t2.join()
    
    final_list = []
    for stock in STOCKS_CONFIG:
        item = {**stock}
        # 填充价格
        market_data = None
        if stock['sina_code'] and stock['sina_code'] in sina_data:
            market_data = sina_data[stock['sina_code']]
        elif stock['ticker'] in yahoo_data:
            market_data = yahoo_data[stock['ticker']]
            
        if market_data: item.update(market_data)
        else: item.update({"currentPrice": "-", "changePercent": 0, "changeAmount": 0, "error": True})
        
        # 填充新闻 (从缓存读取)
        if stock["id"] in NEWS_CACHE:
            item["news"] = NEWS_CACHE[stock["id"]]
        else:
            item["news"] = {"title": "正在获取最新资讯...", "link": "#"}
            
        final_list.append(item)
            
    return final_list