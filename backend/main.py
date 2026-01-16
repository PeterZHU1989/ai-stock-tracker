from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import requests
import yfinance as yf
import threading
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import pandas as pd
import random

app = FastAPI()

# 版本标识
APP_VERSION = "2026.01.15.FINAL" 

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. 股票配置池 (完整版：包含新增港股及所有赛道) ---
STOCKS_CONFIG = [
    # ==================== 🇺🇸 美股 (US) ====================
    {"id": "NVDA", "sina_code": "gb_nvda", "ticker": "NVDA", "name": "英伟达", "market": "US", "sector": "hardware", "subSector": "GPU 芯片", "query": "NVIDIA stock news"},
    {"id": "AMD", "sina_code": "gb_amd", "ticker": "AMD", "name": "超微半导体", "market": "US", "sector": "hardware", "subSector": "GPU 芯片", "query": "AMD stock news"},
    {"id": "AVGO", "sina_code": "gb_avgo", "ticker": "AVGO", "name": "博通", "market": "US", "sector": "hardware", "subSector": "网络/ASIC", "query": "Broadcom stock news"},
    {"id": "MU", "sina_code": "gb_mu", "ticker": "MU", "name": "镁光科技", "market": "US", "sector": "hardware", "subSector": "HBM 存储", "query": "Micron news"},
    {"id": "TSM_US", "sina_code": "gb_tsm", "ticker": "TSM", "name": "台积电(ADR)", "market": "US", "sector": "hardware", "subSector": "晶圆代工", "query": "TSMC stock news"},
    {"id": "SMCI", "sina_code": "gb_smci", "ticker": "SMCI", "name": "超微电脑", "market": "US", "sector": "hardware", "subSector": "AI 服务器", "query": "Super Micro news"},
    {"id": "MRVL", "sina_code": "gb_mrvl", "ticker": "MRVL", "name": "Marvell", "market": "US", "sector": "hardware", "subSector": "光/电芯片", "query": "Marvell news"},
    {"id": "APH", "sina_code": "gb_aph", "ticker": "APH", "name": "安费诺", "market": "US", "sector": "hardware", "subSector": "连接器", "query": "Amphenol stock news"},
    {"id": "TEL", "sina_code": "gb_tel", "ticker": "TEL", "name": "泰科电子", "market": "US", "sector": "hardware", "subSector": "连接器", "query": "TE Connectivity news"},
    {"id": "TSLA", "sina_code": "gb_tsla", "ticker": "TSLA", "name": "特斯拉", "market": "US", "sector": "hardware", "subSector": "机器人/Dojo", "query": "Tesla AI news"},
    {"id": "MSFT", "sina_code": "gb_msft", "ticker": "MSFT", "name": "微软", "market": "US", "sector": "application", "subSector": "云/模型", "query": "Microsoft AI"},
    {"id": "GOOGL", "sina_code": "gb_googl", "ticker": "GOOGL", "name": "谷歌", "market": "US", "sector": "application", "subSector": "搜索/模型", "query": "Google Gemini"},
    {"id": "META", "sina_code": "gb_meta", "ticker": "META", "name": "Meta", "market": "US", "sector": "application", "subSector": "社交/模型", "query": "Llama news"},
    {"id": "APP", "sina_code": "gb_app", "ticker": "APP", "name": "AppLovin", "market": "US", "sector": "application", "subSector": "AI 营销", "query": "AppLovin news"},
    {"id": "PLTR", "sina_code": "gb_pltr", "ticker": "PLTR", "name": "Palantir", "market": "US", "sector": "application", "subSector": "数据分析", "query": "Palantir AI"},

    # ==================== 🇨🇳 A股 (CN) ====================
    {"id": "601138", "sina_code": "sh601138", "ticker": "601138.SS", "name": "工业富联", "market": "CN", "sector": "hardware", "subSector": "AI 服务器", "query": "工业富联 新闻"},
    {"id": "300308", "sina_code": "sz300308", "ticker": "300308.SZ", "name": "中际旭创", "market": "CN", "sector": "hardware", "subSector": "光模块", "query": "中际旭创 新闻"},
    {"id": "688041", "sina_code": "sh688041", "ticker": "688041.SS", "name": "海光信息", "market": "CN", "sector": "hardware", "subSector": "AI 芯片", "query": "海光信息 新闻"},
    {"id": "688256", "sina_code": "sh688256", "ticker": "688256.SS", "name": "寒武纪", "market": "CN", "sector": "hardware", "subSector": "AI 芯片", "query": "寒武纪 新闻"},
    {"id": "300394", "sina_code": "sz300394", "ticker": "300394.SZ", "name": "天孚通信", "market": "CN", "sector": "hardware", "subSector": "光器件", "query": "天孚通信 新闻"},
    {"id": "002463", "sina_code": "sz002463", "ticker": "002463.SZ", "name": "沪电股份", "market": "CN", "sector": "hardware", "subSector": "PCB", "query": "沪电股份 新闻"},
    {"id": "688111", "sina_code": "sh688111", "ticker": "688111.SS", "name": "金山办公", "market": "CN", "sector": "application", "subSector": "办公 AI", "query": "金山办公 新闻"},
    {"id": "002230", "sina_code": "sz002230", "ticker": "002230.SZ", "name": "科大讯飞", "market": "CN", "sector": "application", "subSector": "语音/模型", "query": "科大讯飞 新闻"},

    # ==================== 🇭🇰 港股 (HK) ====================
    # --- 硬件 ---
    {"id": "0981", "sina_code": "rt_hk00981", "ticker": "0981.HK", "name": "中芯国际", "market": "HK", "sector": "hardware", "subSector": "晶圆代工", "query": "中芯国际 新闻"},
    {"id": "1888", "sina_code": "rt_hk01888", "ticker": "1888.HK", "name": "建滔积层板", "market": "HK", "sector": "hardware", "subSector": "CCL 覆铜板", "query": "建滔积层板 新闻"},
    {"id": "06166", "sina_code": "rt_hk06166", "ticker": "06166.HK", "name": "剑桥科技", "market": "HK", "sector": "hardware", "subSector": "光模块(H)", "query": "剑桥科技 港股"},
    {"id": "02577", "sina_code": "rt_hk02577", "ticker": "02577.HK", "name": "英诺赛科", "market": "HK", "sector": "hardware", "subSector": "氮化镓", "query": "英诺赛科 新闻"},
    
    # --- 软件/应用 ---
    {"id": "0700", "sina_code": "rt_hk00700", "ticker": "0700.HK", "name": "腾讯控股", "market": "HK", "sector": "application", "subSector": "社交/游戏", "query": "腾讯 混元"},
    {"id": "09988", "sina_code": "rt_hk09988", "ticker": "9988.HK", "name": "阿里巴巴", "market": "HK", "sector": "application", "subSector": "云/电商", "query": "阿里巴巴 阿里云"},
    {"id": "01024", "sina_code": "rt_hk01024", "ticker": "1024.HK", "name": "快手", "market": "HK", "sector": "application", "subSector": "视频 AI", "query": "快手 可灵AI"},
    {"id": "09888", "sina_code": "rt_hk09888", "ticker": "9888.HK", "name": "百度集团", "market": "HK", "sector": "application", "subSector": "搜索/驾驶", "query": "百度 文心一言"},
    {"id": "03888", "sina_code": "rt_hk03888", "ticker": "3888.HK", "name": "金山软件", "market": "HK", "sector": "application", "subSector": "软件/游戏", "query": "金山软件 新闻"},
    {"id": "01357", "sina_code": "rt_hk01357", "ticker": "1357.HK", "name": "美图公司", "market": "HK", "sector": "application", "subSector": "视觉 AI", "query": "美图公司 AI新闻"},
    {"id": "09660", "sina_code": "rt_hk09660", "ticker": "9660.HK", "name": "地平线", "market": "HK", "sector": "application", "subSector": "智驾芯片", "query": "地平线 智驾 新闻"},
    {"id": "02513", "sina_code": "rt_hk02513", "ticker": "02513.HK", "name": "智谱 AI", "market": "HK", "sector": "application", "subSector": "大模型", "query": "智谱AI 新闻"},
    {"id": "00020", "sina_code": "rt_hk00020", "ticker": "0020.HK", "name": "商汤", "market": "HK", "sector": "application", "subSector": "视觉 AI", "query": "商汤科技 新闻"},

    # ==================== 🇹🇼 台股 (TW) ====================
    {"id": "2330", "sina_code": None, "ticker": "2330.TW", "name": "台积电", "market": "TW", "sector": "hardware", "subSector": "晶圆代工", "query": "台积电 财报"},
    {"id": "2317", "sina_code": None, "ticker": "2317.TW", "name": "鸿海", "market": "TW", "sector": "hardware", "subSector": "服务器代工", "query": "鸿海精密 鸿海AI"},
    {"id": "2454", "sina_code": None, "ticker": "2454.TW", "name": "联发科", "market": "TW", "sector": "hardware", "subSector": "IC 设计", "query": "联发科 天玑"},
]

# --- 2. 新闻抓取模块 ---
NEWS_CACHE = {}

def fetch_google_news_rss(query, stock_id):
    lang_params = "&hl=zh-CN&gl=CN&ceid=CN:zh-Hans" if any(x in query for x in ["新闻", "港股", "财报", "科技"]) else "&hl=en-US&gl=US&ceid=US:en"
    rss_url = f"https://news.google.com/rss/search?q={query}{lang_params}"
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = requests.get(rss_url, headers=headers, timeout=8)
        if resp.status_code == 200:
            root = ET.fromstring(resp.content)
            item = root.find(".//item")
            if item is not None:
                return {"title": item.find("title").text.split(" - ")[0], "link": item.find("link").text}
    except: pass
    return None

def background_news_updater():
    print(f">>> 后台新闻刷新线程启动 (Version: {APP_VERSION})...")
    while True:
        stocks = list(STOCKS_CONFIG)
        random.shuffle(stocks)
        for stock in stocks:
            news = fetch_google_news_rss(stock["query"], stock["id"])
            if news: NEWS_CACHE[stock["id"]] = news
            time.sleep(3) 
        time.sleep(1200)

t = threading.Thread(target=background_news_updater, daemon=True)
t.start()

# --- 3. 数据获取引擎 (实时) ---
def fetch_live_data():
    sina_stocks = [s for s in STOCKS_CONFIG if s['sina_code']]
    codes = ",".join([s['sina_code'] for s in sina_stocks])
    results = {}
    try:
        resp = requests.get(f"http://hq.sinajs.cn/list={codes}", headers={"Referer": "http://finance.sina.com.cn/"}, timeout=5)
        content = resp.content.decode('gbk')
        for line in content.splitlines():
            if "=" not in line: continue
            code = line.split('=')[0].split('_str_')[-1]
            data = line.split('=')[1].strip('";').split(',')
            if len(data) < 5: continue
            if code.startswith('gb_'): 
                p, cp, ca = float(data[1]), float(data[2]), float(data[4])
            else:
                p, prev = float(data[3]), float(data[2])
                ca = p - prev
                cp = (ca / prev * 100) if prev else 0
            results[code] = {"currentPrice": round(p, 2), "changePercent": round(cp, 2), "changeAmount": round(ca, 2)}
    except: pass
    # 台股补丁 (Yahoo)
    tw_tickers = [s['ticker'] for s in STOCKS_CONFIG if s['market'] == 'TW']
    if tw_tickers:
        try:
            tw_data = yf.download(tw_tickers, period="2d", interval="1d", group_by='ticker', progress=False)
            for tkr in tw_tickers:
                df = tw_data[tkr] if len(tw_tickers) > 1 else tw_data
                if not df.empty:
                    p, prev = float(df['Close'].iloc[-1]), float(df['Close'].iloc[-2])
                    results[tkr] = {"currentPrice": round(p, 2), "changePercent": round((p-prev)/prev*100, 2)}
        except: pass
    return results

# --- 4. 历史回溯引擎 ---
def fetch_historical_batch(date_str):
    tickers = [s['ticker'] for s in STOCKS_CONFIG]
    start_dt = datetime.strptime(date_str, "%Y-%m-%d")
    end_dt = start_dt + timedelta(days=1)
    # 获取目标日前后几日数据以确保能计算涨幅
    search_start = start_dt - timedelta(days=7) 
    
    results = {}
    try:
        print(f"[{APP_VERSION}] 查询历史日期: {date_str}")
        data = yf.download(tickers, start=search_start, end=end_dt, group_by='ticker', progress=False)
        
        for stock in STOCKS_CONFIG:
            tkr = stock['ticker']
            df = data[tkr] if len(tickers) > 1 else data
            df_target = df[df.index <= pd.Timestamp(date_str)]
            
            if df_target.empty: continue
            
            current_row = df_target.iloc[-1]
            # 检查是否休市：如果该日数据日期不匹配，说明当天没开盘
            if current_row.name.date() != start_dt.date():
                results[tkr] = {"error": True, "note": "休市"}
                continue
                
            close_p = float(current_row['Close'])
            if len(df_target) > 1:
                prev_close = float(df_target.iloc[-2]['Close'])
                cp = (close_p - prev_close) / prev_close * 100
            else:
                cp = 0.0
            
            results[tkr] = {
                "currentPrice": round(close_p, 2),
                "changePercent": round(cp, 2),
                "historicalNote": f"当日收盘价: {round(close_p, 2)}"
            }
    except Exception as e:
        print(f"Historical Error: {e}")
    return results

@app.get("/")
def read_root():
    return {
        "status": "online", 
        "version": APP_VERSION,
        "stocks_count": len(STOCKS_CONFIG)
    }

@app.get("/api/stocks")
def get_stocks(date: str = Query(None)):
    final_list = []
    
    if date:
        # 历史模式
        hist_data = fetch_historical_batch(date)
        for stock in STOCKS_CONFIG:
            item = {**stock}
            m_data = hist_data.get(stock['ticker'])
            if m_data:
                item.update(m_data)
            else:
                item.update({"currentPrice": "-", "changePercent": 0, "error": True})
            final_list.append(item)
    else:
        # 实时模式
        live_data = fetch_live_data()
        for stock in STOCKS_CONFIG:
            item = {**stock}
            m_data = live_data.get(stock['sina_code']) if stock['sina_code'] else live_data.get(stock['ticker'])
            if m_data:
                item.update(m_data)
            else:
                item.update({"currentPrice": "-", "changePercent": 0, "error": True})
            item["news"] = NEWS_CACHE.get(stock["id"], {"title": "同步中...", "link": "#"})
            final_list.append(item)
            
    return final_list