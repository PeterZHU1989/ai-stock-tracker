import re
import json
import time
import random
import threading
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 版本标记，用于前端校验
APP_VERSION = "2026.01.15.SINA_ENGINE_FULL_LIST"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. 股票配置池 (完整恢复版) ---
STOCKS_CONFIG = [
    # ==================== 🇺🇸 美国市场 (US) ====================
    {"id": "NVDA", "sina_code": "gb_nvda", "ticker": "NVDA", "name": "英伟达", "market": "US", "sector": "hardware", "subSector": "GPU 芯片", "query": "NVIDIA stock news"},
    {"id": "AMD", "sina_code": "gb_amd", "ticker": "AMD", "name": "超微半导体", "market": "US", "sector": "hardware", "subSector": "GPU 芯片", "query": "AMD stock news"},
    {"id": "AVGO", "sina_code": "gb_avgo", "ticker": "AVGO", "name": "博通", "market": "US", "sector": "hardware", "subSector": "网络/ASIC", "query": "Broadcom stock news"},
    {"id": "MU", "sina_code": "gb_mu", "ticker": "MU", "name": "镁光科技", "market": "US", "sector": "hardware", "subSector": "HBM 存储", "query": "Micron news"},
    {"id": "TSM_US", "sina_code": "gb_tsm", "ticker": "TSM", "name": "台积电(ADR)", "market": "US", "sector": "hardware", "subSector": "晶圆代工", "query": "TSMC news"},
    {"id": "SMCI", "sina_code": "gb_smci", "ticker": "SMCI", "name": "超微电脑", "market": "US", "sector": "hardware", "subSector": "AI 服务器", "query": "Supermicro news"},
    {"id": "MRVL", "sina_code": "gb_mrvl", "ticker": "MRVL", "name": "Marvell", "market": "US", "sector": "hardware", "subSector": "光/电芯片", "query": "Marvell news"},
    {"id": "APH", "sina_code": "gb_aph", "ticker": "APH", "name": "安费诺", "market": "US", "sector": "hardware", "subSector": "连接器", "query": "Amphenol stock news"},
    {"id": "TEL", "sina_code": "gb_tel", "ticker": "TEL", "name": "泰科电子", "market": "US", "sector": "hardware", "subSector": "连接器", "query": "TE Connectivity news"},
    {"id": "TSLA", "sina_code": "gb_tsla", "ticker": "TSLA", "name": "特斯拉", "market": "US", "sector": "hardware", "subSector": "机器人/Dojo", "query": "Tesla AI news"},
    {"id": "MSFT", "sina_code": "gb_msft", "ticker": "MSFT", "name": "微软", "market": "US", "sector": "application", "subSector": "云/模型", "query": "Microsoft AI"},
    {"id": "GOOGL", "sina_code": "gb_googl", "ticker": "GOOGL", "name": "谷歌", "market": "US", "sector": "application", "subSector": "搜索/模型", "query": "Google Gemini"},
    {"id": "META", "sina_code": "gb_meta", "ticker": "META", "name": "Meta", "market": "US", "sector": "application", "subSector": "社交/模型", "query": "Meta Llama"},
    {"id": "APP", "sina_code": "gb_app", "ticker": "APP", "name": "AppLovin", "market": "US", "sector": "application", "subSector": "AI 营销", "query": "AppLovin news"},
    {"id": "PLTR", "sina_code": "gb_pltr", "ticker": "PLTR", "name": "Palantir", "market": "US", "sector": "application", "subSector": "数据分析", "query": "Palantir AI"},

    # ==================== 🇨🇳 中国 A 股 (CN) ====================
    {"id": "601138", "sina_code": "sh601138", "ticker": "601138.SS", "name": "工业富联", "market": "CN", "sector": "hardware", "subSector": "AI 服务器", "query": "工业富联 新闻"},
    {"id": "300308", "sina_code": "sz300308", "ticker": "300308.SZ", "name": "中际旭创", "market": "CN", "sector": "hardware", "subSector": "光模块", "query": "中际旭创 新闻"},
    {"id": "688041", "sina_code": "sh688041", "ticker": "688041.SS", "name": "海光信息", "market": "CN", "sector": "hardware", "subSector": "AI 芯片", "query": "海光信息 新闻"},
    {"id": "688256", "sina_code": "sh688256", "ticker": "688256.SS", "name": "寒武纪", "market": "CN", "sector": "hardware", "subSector": "AI 芯片", "query": "寒武纪 新闻"},
    {"id": "300394", "sina_code": "sz300394", "ticker": "300394.SZ", "name": "天孚通信", "market": "CN", "sector": "hardware", "subSector": "光器件", "query": "天孚通信 新闻"},
    {"id": "002463", "sina_code": "sz002463", "ticker": "002463.SZ", "name": "沪电股份", "market": "CN", "sector": "hardware", "subSector": "PCB", "query": "沪电股份 新闻"},
    {"id": "688111", "sina_code": "sh688111", "ticker": "688111.SS", "name": "金山办公", "market": "CN", "sector": "application", "subSector": "办公 AI", "query": "金山办公 新闻"},
    {"id": "002230", "sina_code": "sz002230", "ticker": "002230.SZ", "name": "科大讯飞", "market": "CN", "sector": "application", "subSector": "语音/模型", "query": "科大讯飞 新闻"},

    # ==================== 🇭🇰 中国香港 (HK) ====================
    {"id": "0981", "sina_code": "rt_hk00981", "ticker": "0981.HK", "name": "中芯国际", "market": "HK", "sector": "hardware", "subSector": "晶圆代工", "query": "中芯国际 新闻"},
    {"id": "1888", "sina_code": "rt_hk01888", "ticker": "1888.HK", "name": "建滔积层板", "market": "HK", "sector": "hardware", "subSector": "CCL 覆铜板", "query": "建滔积层板 新闻"},
    {"id": "06166", "sina_code": "rt_hk06166", "ticker": "06166.HK", "name": "剑桥科技", "market": "HK", "sector": "hardware", "subSector": "光模块(H)", "query": "剑桥科技 港股"},
    {"id": "02577", "sina_code": "rt_hk02577", "ticker": "02577.HK", "name": "英诺赛科", "market": "HK", "sector": "hardware", "subSector": "氮化镓", "query": "英诺赛科 新闻"},
    {"id": "0700", "sina_code": "rt_hk00700", "ticker": "0700.HK", "name": "腾讯控股", "market": "HK", "sector": "application", "subSector": "社交/游戏", "query": "腾讯 混元"},
    {"id": "09988", "sina_code": "rt_hk09988", "ticker": "9988.HK", "name": "阿里巴巴", "market": "HK", "sector": "application", "subSector": "云/电商", "query": "阿里巴巴 阿里云"},
    {"id": "01024", "sina_code": "rt_hk01024", "ticker": "1024.HK", "name": "快手", "market": "HK", "sector": "application", "subSector": "视频 AI", "query": "快手 可灵AI"},
    {"id": "09888", "sina_code": "rt_hk09888", "ticker": "9888.HK", "name": "百度集团", "market": "HK", "sector": "application", "subSector": "搜索/驾驶", "query": "百度 文心一言"},
    {"id": "03888", "sina_code": "rt_hk03888", "ticker": "3888.HK", "name": "金山软件", "market": "HK", "sector": "application", "subSector": "软件/游戏", "query": "金山软件 新闻"},
    {"id": "01357", "sina_code": "rt_hk01357", "ticker": "1357.HK", "name": "美图公司", "market": "HK", "sector": "application", "subSector": "视觉 AI", "query": "美图公司 AI新闻"},
    {"id": "09660", "sina_code": "rt_hk09660", "ticker": "9660.HK", "name": "地平线", "market": "HK", "sector": "application", "subSector": "智驾芯片", "query": "地平线 智驾 新闻"},
    {"id": "02513", "sina_code": "rt_hk02513", "ticker": "02513.HK", "name": "智谱 AI", "market": "HK", "sector": "application", "subSector": "大模型", "query": "智谱AI 新闻"},
    {"id": "00020", "sina_code": "rt_hk00020", "ticker": "0020.HK", "name": "商汤", "market": "HK", "sector": "application", "subSector": "视觉 AI", "query": "商汤科技 新闻"},

    # ==================== 🇹🇼 中国台湾 (TW) ====================
    {"id": "2330", "sina_code": None, "ticker": "2330.TW", "name": "台积电", "market": "TW", "sector": "hardware", "subSector": "晶圆代工", "query": "台积电 财报"},
    {"id": "2317", "sina_code": None, "ticker": "2317.TW", "name": "鸿海", "market": "TW", "sector": "hardware", "subSector": "服务器代工", "query": "鸿海精密 鸿海AI"},
    {"id": "2454", "sina_code": None, "ticker": "2454.TW", "name": "联发科", "market": "TW", "sector": "hardware", "subSector": "IC 设计", "query": "联发科 天玑"},
]

# --- 2. 实时新闻缓存 ---
NEWS_CACHE = {}

def fetch_google_news(query, stock_id):
    lang = "&hl=zh-CN&gl=CN&ceid=CN:zh-Hans" if any(x in query for x in ["新闻", "港股", "财报", "科技"]) else "&hl=en-US&gl=US&ceid=US:en"
    url = f"https://news.google.com/rss/search?q={query}{lang}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            root = ET.fromstring(resp.content)
            item = root.find(".//item")
            if item is not None:
                return {"title": item.find("title").text.split(" - ")[0], "link": item.find("link").text}
    except: pass
    return None

def background_news_worker():
    while True:
        stocks = list(STOCKS_CONFIG)
        random.shuffle(stocks)
        for stock in stocks:
            news = fetch_google_news(stock["query"], stock["id"])
            if news: NEWS_CACHE[stock["id"]] = news
            time.sleep(3) 
        time.sleep(1200)

threading.Thread(target=background_news_worker, daemon=True).start()

# --- 3. 核心功能：新浪财经 K 线正则清洗引擎 (处理历史回溯) ---
def fetch_sina_historical_single(sina_code, target_date_str):
    if not sina_code: return None # 台股等无 sina_code 的标的暂不支持 K 线回溯
    try:
        if sina_code.startswith(('sh', 'sz')):
            url = f"http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={sina_code}&scale=240&ma=no&datalen=30"
        elif sina_code.startswith('rt_hk'):
            symbol = sina_code.replace('rt_hk', '')
            url = f"http://quotes.sina.cn/hk/api/jsonp_v2.php/var%20_code=/HK_StockService.getHKDayKLine?symbol={symbol}"
        elif sina_code.startswith('gb_'):
            symbol = sina_code.replace('gb_', '').upper()
            url = f"http://stock.finance.sina.com.cn/usstock/api/jsonp.php/IO.StockService.getKLineData?symbol={symbol}&type=day"
        else: return None

        headers = {"Referer": "http://finance.sina.com.cn/"}
        resp = requests.get(url, headers=headers, timeout=10)
        content = resp.text

        # 正则清洗：提取 [...] 数组并补全 A 股 Key 引号
        match = re.search(r'\[.*\]', content, re.DOTALL)
        if not match: return None
        json_str = match.group()
        if sina_code.startswith(('sh', 'sz')):
            json_str = re.sub(r'([{,])\s*([a-zA-Z0-9_]+)\s*:', r'\1"\2":', json_str)

        data = json.loads(json_str)
        target_dt = datetime.strptime(target_date_str, "%Y-%m-%d").date()
        
        selected_row, prev_row = None, None
        for i, row in enumerate(data):
            row_date_raw = row.get('day') or row.get('d')
            row_dt = datetime.strptime(row_date_raw.split(' ')[0], "%Y-%m-%d").date()
            if row_dt <= target_dt:
                selected_row = row
                if i > 0: prev_row = data[i-1]
            else: break
        
        if selected_row:
            close_p = float(selected_row.get('close') or selected_row.get('c'))
            ref_p = float(prev_row.get('close') or prev_row.get('c')) if prev_row else close_p
            change_p = ((close_p - ref_p) / ref_p * 100) if ref_p else 0
            actual_date = (selected_row.get('day') or selected_row.get('d')).split(' ')[0]
            note = f"收盘价: {close_p}"
            if actual_date != target_date_str:
                note = f"⚠️ 选定日休市，显示最近交易日({actual_date})数据。"
            return {"currentPrice": round(close_p, 2), "changePercent": round(change_p, 2), "historicalNote": note}
    except: pass
    return None

# --- 4. 实时行情抓取 ---
def fetch_live_data():
    results = {}
    # 1. 批量请求新浪
    sina_codes = [s['sina_code'] for s in STOCKS_CONFIG if s['sina_code']]
    if sina_codes:
        try:
            url = f"http://hq.sinajs.cn/list={','.join(sina_codes)}"
            resp = requests.get(url, headers={"Referer": "http://finance.sina.com.cn/"}, timeout=5)
            content = resp.content.decode('gbk')
            for line in content.splitlines():
                if "=" not in line: continue
                code = line.split('=')[0].split('_str_')[-1]
                data = line.split('=')[1].strip('";').split(',')
                if len(data) < 10: continue
                if code.startswith('gb_'): p, cp = float(data[1]), float(data[2])
                elif code.startswith('rt_hk'): p, cp = float(data[6]), float(data[8])
                else: 
                    p, prev = float(data[3]), float(data[2])
                    cp = (p - prev) / prev * 100 if prev else 0
                results[code] = {"currentPrice": round(p, 2), "changePercent": round(cp, 2)}
        except: pass

    # 2. 台股特殊处理 (从 Yahoo 获取实时)
    tw_tickers = [s['ticker'] for s in STOCKS_CONFIG if s['market'] == 'TW']
    if tw_tickers:
        import yfinance as yf
        try:
            tw_data = yf.download(tw_tickers, period="2d", interval="1d", group_by='ticker', progress=False)
            for tkr in tw_tickers:
                df = tw_data[tkr] if len(tw_tickers) > 1 else tw_data
                if not df.empty:
                    p = float(df['Close'].iloc[-1])
                    prev = float(df['Close'].iloc[-2]) if len(df) > 1 else p
                    results[tkr] = {"currentPrice": round(p, 2), "changePercent": round((p-prev)/prev*100, 2)}
        except: pass
    return results

# --- 5. API 路由 ---
@app.get("/")
def home():
    return {"status": "online", "engine": "Sina Ultimate", "version": APP_VERSION, "count": len(STOCKS_CONFIG)}

@app.get("/api/stocks")
def get_stocks_api(date: str = Query(None)):
    final_list = []
    if date:
        results = {}
        def task(stock):
            res = fetch_sina_historical_single(stock['sina_code'], date)
            if res: results[stock['id']] = res
        threads = [threading.Thread(target=task, args=(s,)) for s in STOCKS_CONFIG]
        for t in threads: t.start()
        for t in threads: t.join()
        for s in STOCKS_CONFIG:
            item = {**s}
            h_data = results.get(s['id'])
            if h_data: item.update(h_data)
            else: item.update({"currentPrice": "-", "changePercent": 0, "error": True})
            final_list.append(item)
    else:
        live_data = fetch_live_data()
        for s in STOCKS_CONFIG:
            item = {**s}
            l_data = live_data.get(s['sina_code'] or s['ticker'])
            if l_data: item.update(l_data)
            else: item.update({"currentPrice": "-", "changePercent": 0, "error": True})
            item["news"] = NEWS_CACHE.get(s["id"], {"title": "同步中...", "link": "#"})
            final_list.append(item)
    return final_list

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)