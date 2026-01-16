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

# 初始化 FastAPI
app = FastAPI()

# 版本标记：用于检查部署是否刷新
APP_VERSION = "2026.01.15.RENDER_OPTIMIZED"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. 股票配置池 ---
STOCKS_CONFIG = [
    {"id": "NVDA", "sina_code": "gb_nvda", "ticker": "NVDA", "name": "英伟达", "market": "US", "sector": "hardware", "subSector": "GPU 芯片", "query": "NVIDIA stock news"},
    {"id": "AMD", "sina_code": "gb_amd", "ticker": "AMD", "name": "超微半导体", "market": "US", "sector": "hardware", "subSector": "GPU 芯片", "query": "AMD stock news"},
    {"id": "AVGO", "sina_code": "gb_avgo", "ticker": "AVGO", "name": "博通", "market": "US", "sector": "hardware", "subSector": "网络/ASIC", "query": "Broadcom stock news"},
    {"id": "MU", "sina_code": "gb_mu", "ticker": "MU", "name": "镁光科技", "market": "US", "sector": "hardware", "subSector": "HBM 存储", "query": "Micron news"},
    {"id": "TSM_US", "sina_code": "gb_tsm", "ticker": "TSM", "name": "台积电(ADR)", "market": "US", "sector": "hardware", "subSector": "晶圆代工", "query": "TSMC news"},
    {"id": "SMCI", "sina_code": "gb_smci", "ticker": "SMCI", "name": "超微电脑", "market": "US", "sector": "hardware", "subSector": "AI 服务器", "query": "Supermicro news"},
    {"id": "MRVL", "sina_code": "gb_mrvl", "ticker": "MRVL", "name": "Marvell", "market": "US", "sector": "hardware", "subSector": "光/电芯片", "query": "Marvell news"},
    {"id": "APH", "sina_code": "gb_aph", "ticker": "APH", "name": "安费诺", "market": "US", "sector": "hardware", "subSector": "连接器", "query": "Amphenol stock"},
    {"id": "TEL", "sina_code": "gb_tel", "ticker": "TEL", "name": "泰科电子", "market": "US", "sector": "hardware", "subSector": "连接器", "query": "TE Connectivity"},
    {"id": "DELL", "sina_code": "gb_dell", "ticker": "DELL", "name": "戴尔科技", "market": "US", "sector": "hardware", "subSector": "AI PC/服务器", "query": "Dell AI"},
    {"id": "TSLA", "sina_code": "gb_tsla", "ticker": "TSLA", "name": "特斯拉", "market": "US", "sector": "hardware", "subSector": "机器人/Dojo", "query": "Tesla AI"},
    {"id": "MSFT", "sina_code": "gb_msft", "ticker": "MSFT", "name": "微软", "market": "US", "sector": "application", "subSector": "云/模型", "query": "Microsoft AI"},
    {"id": "GOOGL", "sina_code": "gb_googl", "ticker": "GOOGL", "name": "谷歌", "market": "US", "sector": "application", "subSector": "搜索/模型", "query": "Google Gemini"},
    {"id": "META", "sina_code": "gb_meta", "ticker": "META", "name": "Meta", "market": "US", "sector": "application", "subSector": "社交/模型", "query": "Meta Llama"},
    {"id": "APP", "sina_code": "gb_app", "ticker": "APP", "name": "AppLovin", "market": "US", "sector": "application", "subSector": "AI 营销", "query": "AppLovin news"},
    {"id": "PLTR", "sina_code": "gb_pltr", "ticker": "PLTR", "name": "Palantir", "market": "US", "sector": "application", "subSector": "数据分析", "query": "Palantir AI"},
    {"id": "601138", "sina_code": "sh601138", "ticker": "601138.SS", "name": "工业富联", "market": "CN", "sector": "hardware", "subSector": "AI 服务器", "query": "工业富联"},
    {"id": "300308", "sina_code": "sz300308", "ticker": "300308.SZ", "name": "中际旭创", "market": "CN", "sector": "hardware", "subSector": "光模块", "query": "中际旭创"},
    {"id": "688041", "sina_code": "sh688041", "ticker": "688041.SS", "name": "海光信息", "market": "CN", "sector": "hardware", "subSector": "AI 芯片", "query": "海光信息"},
    {"id": "688256", "sina_code": "sh688256", "ticker": "688256.SS", "name": "寒武纪", "market": "CN", "sector": "hardware", "subSector": "AI 芯片", "query": "寒武纪"},
    {"id": "300394", "sina_code": "sz300394", "ticker": "300394.SZ", "name": "天孚通信", "market": "CN", "sector": "hardware", "subSector": "光器件", "query": "天孚通信"},
    {"id": "002463", "sina_code": "sz002463", "ticker": "002463.SZ", "name": "沪电股份", "market": "CN", "sector": "hardware", "subSector": "PCB", "query": "沪电股份"},
    {"id": "688111", "sina_code": "sh688111", "ticker": "688111.SS", "name": "金山办公", "market": "CN", "sector": "application", "subSector": "办公 AI", "query": "金山办公"},
    {"id": "002230", "sina_code": "sz002230", "ticker": "002230.SZ", "name": "科大讯飞", "market": "CN", "sector": "application", "subSector": "语音/模型", "query": "科大讯飞"},
    {"id": "0981", "sina_code": "rt_hk00981", "ticker": "0981.HK", "name": "中芯国际", "market": "HK", "sector": "hardware", "subSector": "晶圆代工", "query": "中芯国际"},
    {"id": "1888", "sina_code": "rt_hk01888", "ticker": "1888.HK", "name": "建滔积层板", "market": "HK", "sector": "hardware", "subSector": "CCL 覆铜板", "query": "建滔积层板"},
    {"id": "06166", "sina_code": "rt_hk06166", "ticker": "06166.HK", "name": "剑桥科技", "market": "HK", "sector": "hardware", "subSector": "光模块(H)", "query": "剑桥科技"},
    {"id": "02577", "sina_code": "rt_hk02577", "ticker": "02577.HK", "name": "英诺赛科", "market": "HK", "sector": "hardware", "subSector": "氮化镓", "query": "英诺赛科"},
    {"id": "0700", "sina_code": "rt_hk00700", "ticker": "0700.HK", "name": "腾讯控股", "market": "HK", "sector": "application", "subSector": "社交/游戏", "query": "腾讯 混元"},
    {"id": "09988", "sina_code": "rt_hk09988", "ticker": "09988.HK", "name": "阿里巴巴", "market": "HK", "sector": "application", "subSector": "云/电商", "query": "阿里巴巴"},
    {"id": "01024", "sina_code": "rt_hk01024", "ticker": "1024.HK", "name": "快手", "market": "HK", "sector": "application", "subSector": "视频 AI", "query": "快手 可灵"},
    {"id": "09888", "sina_code": "rt_hk09888", "ticker": "9888.HK", "name": "百度集团", "market": "HK", "sector": "application", "subSector": "搜索/驾驶", "query": "百度 文心"},
    {"id": "03888", "sina_code": "rt_hk03888", "ticker": "3888.HK", "name": "金山软件", "market": "HK", "sector": "application", "subSector": "软件/游戏", "query": "金山软件"},
    {"id": "01357", "sina_code": "rt_hk01357", "ticker": "1357.HK", "name": "美图公司", "market": "HK", "sector": "application", "subSector": "视觉 AI", "query": "美图公司"},
    {"id": "09660", "sina_code": "rt_hk09660", "ticker": "9660.HK", "name": "地平线", "market": "HK", "sector": "application", "subSector": "智驾芯片", "query": "地平线"},
    {"id": "02513", "sina_code": "rt_hk02513", "ticker": "02513.HK", "name": "智谱 AI", "market": "HK", "sector": "application", "subSector": "大模型", "query": "智谱AI"},
    {"id": "00020", "sina_code": "rt_hk00020", "ticker": "0020.HK", "name": "商汤", "market": "HK", "sector": "application", "subSector": "视觉 AI", "query": "商汤科技"},
    {"id": "2330", "sina_code": None, "ticker": "2330.TW", "name": "台积电", "market": "TW", "sector": "hardware", "subSector": "晶圆代工", "query": "TSMC Taiwan"},
    {"id": "2317", "sina_code": None, "ticker": "2317.TW", "name": "鸿海", "market": "TW", "sector": "hardware", "subSector": "服务器代工", "query": "Foxconn AI"},
    {"id": "2454", "sina_code": None, "ticker": "2454.TW", "name": "联发科", "market": "TW", "sector": "hardware", "subSector": "IC 设计", "query": "MediaTek AI"},
]

# --- 2. 新闻抓取与后台线程 ---
NEWS_CACHE = {}

def fetch_google_news(query, stock_id):
    lang = "&hl=zh-CN&gl=CN&ceid=CN:zh-Hans" if any(x in query for x in ["新", "阿", "腾", "中", "台"]) else "&hl=en-US&gl=US&ceid=US:en"
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

def news_worker():
    while True:
        shuffled = list(STOCKS_CONFIG)
        random.shuffle(shuffled)
        for stock in shuffled:
            news = fetch_google_news(stock["query"], stock["id"])
            if news: NEWS_CACHE[stock["id"]] = news
            time.sleep(3)
        time.sleep(1200)

# 启动后台新闻线程
threading.Thread(target=news_worker, daemon=True).start()

# --- 3. 数据抓取逻辑 (正则引擎) ---
def fetch_sina_historical_single(sina_code, target_date_str):
    if not sina_code: return None
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

        resp = requests.get(url, headers={"Referer": "http://finance.sina.com.cn/"}, timeout=10)
        content = resp.text
        match = re.search(r'\[.*\]', content, re.DOTALL)
        if not match: return None
        json_str = match.group()
        if sina_code.startswith(('sh', 'sz')):
            json_str = re.sub(r'([{,])\s*([a-zA-Z0-9_]+)\s*:', r'\1"\2":', json_str)
        
        data = json.loads(json_str)
        target_dt = datetime.strptime(target_date_str, "%Y-%m-%d").date()
        
        selected, prev = None, None
        for i, row in enumerate(data):
            r_date = row.get('day') or row.get('d')
            r_dt = datetime.strptime(r_date.split(' ')[0], "%Y-%m-%d").date()
            if r_dt <= target_dt:
                selected = row
                if i > 0: prev = data[i-1]
            else: break
        
        if selected:
            cp = float(selected.get('close') or selected.get('c'))
            ref = float(prev.get('close') or prev.get('c')) if prev else cp
            chg = ((cp - ref) / ref * 100) if ref else 0
            act_date = (selected.get('day') or selected.get('d')).split(' ')[0]
            note = f"收盘: {cp}" if act_date == target_date_str else f"⚠️ 休市, 显示 {act_date} 数据。"
            return {"currentPrice": round(cp, 2), "changePercent": round(chg, 2), "historicalNote": note}
    except: pass
    return None

def fetch_live_data():
    res = {}
    sina_codes = [s['sina_code'] for s in STOCKS_CONFIG if s['sina_code']]
    if sina_codes:
        try:
            url = f"http://hq.sinajs.cn/list={','.join(sina_codes)}"
            resp = requests.get(url, headers={"Referer": "http://finance.sina.com.cn/"}, timeout=5)
            lines = resp.content.decode('gbk').splitlines()
            for line in lines:
                if "=" not in line: continue
                code = line.split('=')[0].split('_str_')[-1]
                data = line.split('=')[1].strip('";').split(',')
                if len(data) < 10: continue
                if code.startswith('gb_'): p, cp = float(data[1]), float(data[2])
                elif code.startswith('rt_hk'): p, cp = float(data[6]), float(data[8])
                else:
                    p, prev = float(data[3]), float(data[2])
                    cp = (p - prev) / prev * 100 if prev else 0
                res[code] = {"currentPrice": round(p, 2), "changePercent": round(cp, 2)}
        except: pass
    
    # 台股补丁 (由于 Render 容易封 yfinance，这里加个 try)
    try:
        import yfinance as yf
        tw_tkrs = [s['ticker'] for s in STOCKS_CONFIG if s['market'] == 'TW']
        tw_data = yf.download(tw_tkrs, period="2d", interval="1d", group_by='ticker', progress=False)
        for tkr in tw_tkrs:
            df = tw_data[tkr] if len(tw_tkrs) > 1 else tw_data
            if not df.empty:
                p = float(df['Close'].iloc[-1])
                prev = float(df['Close'].iloc[-2]) if len(df) > 1 else p
                res[tkr] = {"currentPrice": round(p, 2), "changePercent": round((p-prev)/prev*100, 2)}
    except: pass
    return res

# --- 4. API 路由 ---
@app.get("/")
def health_check():
    """Render 用于检测服务是否存活的接口"""
    return {"status": "online", "version": APP_VERSION, "stocks_count": len(STOCKS_CONFIG)}

@app.get("/api/stocks")
def get_stocks(date: str = Query(None)):
    final = []
    if date:
        # 历史模式
        results = {}
        def task(s):
            r = fetch_sina_historical_single(s['sina_code'], date)
            if r: results[s['id']] = r
        threads = [threading.Thread(target=task, args=(s,)) for s in STOCKS_CONFIG]
        for t in threads: t.start()
        for t in threads: t.join()
        for s in STOCKS_CONFIG:
            item = {**s}
            h = results.get(s['id'])
            if h: item.update(h)
            else: item.update({"currentPrice": "-", "changePercent": 0, "error": True})
            final.append(item)
    else:
        # 实时模式
        live = fetch_live_data()
        for s in STOCKS_CONFIG:
            item = {**s}
            l = live.get(s['sina_code'] or s['ticker'])
            if l: item.update(l)
            else: item.update({"currentPrice": "-", "changePercent": 0, "error": True})
            item["news"] = NEWS_CACHE.get(s["id"], {"title": "正在抓取最新热点...", "link": "#"})
            final.append(item)
    return final

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)