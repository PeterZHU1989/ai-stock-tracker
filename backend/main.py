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
APP_VERSION = "2026.01.15.SINA_ENGINE_ULTIMATE"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. 股票配置池 (确保与前端同步) ---
STOCKS_CONFIG = [
    # 美国市场 (US)
    {"id": "NVDA", "sina_code": "gb_nvda", "ticker": "NVDA", "name": "英伟达", "market": "US", "sector": "hardware", "subSector": "GPU 芯片", "query": "NVIDIA stock"},
    {"id": "AMD", "sina_code": "gb_amd", "ticker": "AMD", "name": "超微半导体", "market": "US", "sector": "hardware", "subSector": "GPU 芯片", "query": "AMD stock"},
    {"id": "AVGO", "sina_code": "gb_avgo", "ticker": "AVGO", "name": "博通", "market": "US", "sector": "hardware", "subSector": "网络/ASIC", "query": "Broadcom stock"},
    {"id": "MU", "sina_code": "gb_mu", "ticker": "MU", "name": "镁光科技", "market": "US", "sector": "hardware", "subSector": "HBM 存储", "query": "Micron technology"},
    {"id": "TSM_US", "sina_code": "gb_tsm", "ticker": "TSM", "name": "台积电(ADR)", "market": "US", "sector": "hardware", "subSector": "晶圆代工", "query": "TSMC news"},
    {"id": "SMCI", "sina_code": "gb_smci", "ticker": "SMCI", "name": "超微电脑", "market": "US", "sector": "hardware", "subSector": "AI 服务器", "query": "Supermicro news"},
    {"id": "TSLA", "sina_code": "gb_tsla", "ticker": "TSLA", "name": "特斯拉", "market": "US", "sector": "hardware", "subSector": "机器人/Dojo", "query": "Tesla AI"},
    {"id": "MSFT", "sina_code": "gb_msft", "ticker": "MSFT", "name": "微软", "market": "US", "sector": "application", "subSector": "云/模型", "query": "Microsoft AI"},
    {"id": "GOOGL", "sina_code": "gb_googl", "ticker": "GOOGL", "name": "谷歌", "market": "US", "sector": "application", "subSector": "搜索/模型", "query": "Google Gemini"},
    {"id": "META", "sina_code": "gb_meta", "ticker": "META", "name": "Meta", "market": "US", "sector": "application", "subSector": "社交/模型", "query": "Meta Llama"},
    
    # 中国 A 股 (CN)
    {"id": "601138", "sina_code": "sh601138", "ticker": "601138.SS", "name": "工业富联", "market": "CN", "sector": "hardware", "subSector": "AI 服务器", "query": "工业富联 新闻"},
    {"id": "300308", "sina_code": "sz300308", "ticker": "300308.SZ", "name": "中际旭创", "market": "CN", "sector": "hardware", "subSector": "光模块", "query": "中际旭创"},
    {"id": "688041", "sina_code": "sh688041", "ticker": "688041.SS", "name": "海光信息", "market": "CN", "sector": "hardware", "subSector": "AI 芯片", "query": "海光信息"},
    {"id": "688256", "sina_code": "sh688256", "ticker": "688256.SS", "name": "寒武纪", "market": "CN", "sector": "hardware", "subSector": "AI 芯片", "query": "寒武纪 新闻"},
    {"id": "688111", "sina_code": "sh688111", "ticker": "688111.SS", "name": "金山办公", "market": "CN", "sector": "application", "subSector": "办公软件", "query": "WPS AI"},
    
    # 中国香港 (HK)
    {"id": "0981", "sina_code": "rt_hk00981", "ticker": "0981.HK", "name": "中芯国际", "market": "HK", "sector": "hardware", "subSector": "晶圆代工", "query": "中芯国际"},
    {"id": "0700", "sina_code": "rt_hk00700", "ticker": "0700.HK", "name": "腾讯控股", "market": "HK", "sector": "application", "subSector": "社交/游戏", "query": "腾讯 混元"},
    {"id": "09988", "sina_code": "rt_hk09988", "ticker": "9988.HK", "name": "阿里巴巴", "market": "HK", "sector": "application", "subSector": "云/电商", "query": "阿里云 AI"},
    {"id": "09660", "sina_code": "rt_hk09660", "ticker": "9660.HK", "name": "地平线机器人", "market": "HK", "sector": "hardware", "subSector": "智驾芯片", "query": "地平线机器人"},
]

# --- 2. 实时新闻缓存 ---
NEWS_CACHE = {}

def fetch_google_news(query, stock_id):
    # 根据查询词自动选择语言偏好
    lang = "&hl=zh-CN&gl=CN&ceid=CN:zh-Hans" if any(x in query for x in ["新闻", "阿里巴巴", "腾讯"]) else "&hl=en-US&gl=US&ceid=US:en"
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
        for stock in STOCKS_CONFIG:
            news = fetch_google_news(stock["query"], stock["id"])
            if news: NEWS_CACHE[stock["id"]] = news
            time.sleep(2) # 礼貌抓取
        time.sleep(1800) # 每半小时刷新

threading.Thread(target=background_news_worker, daemon=True).start()

# --- 3. 核心功能：新浪财经历史 K 线抓取与正则清洗 ---
def fetch_sina_historical_single(sina_code, target_date_str):
    """
    抓取新浪财经 K 线数据。
    新浪返回的是非标准 JSON (JS 变量包裹或 Key 无引号)，必须用正则清洗。
    """
    try:
        # A 股 K 线接口
        if sina_code.startswith(('sh', 'sz')):
            url = f"http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={sina_code}&scale=240&ma=no&datalen=30"
        # 港股 K 线接口 (JS 重定向接口)
        elif sina_code.startswith('rt_hk'):
            symbol = sina_code.replace('rt_hk', '')
            url = f"http://quotes.sina.cn/hk/api/jsonp_v2.php/var%20_code=/HK_StockService.getHKDayKLine?symbol={symbol}"
        # 美股 K 线接口
        elif sina_code.startswith('gb_'):
            symbol = sina_code.replace('gb_', '').upper()
            url = f"http://stock.finance.sina.com.cn/usstock/api/jsonp.php/IO.StockService.getKLineData?symbol={symbol}&type=day"
        else:
            return None

        headers = {"Referer": "http://finance.sina.com.cn/"}
        resp = requests.get(url, headers=headers, timeout=10)
        content = resp.text

        # 核心修复：使用正则表达式提取并清洗 JSON 数据
        # 1. 提取中括号内的数组部分
        match = re.search(r'\[.*\]', content, re.DOTALL)
        if not match: return None
        json_str = match.group()

        # 2. 针对 A 股那种没有引号的键名 (如 day: ) 进行特殊处理，使其符合标准 JSON
        if sina_code.startswith(('sh', 'sz')):
            json_str = re.sub(r'([{,])\s*([a-zA-Z0-9_]+)\s*:', r'\1"\2":', json_str)

        data = json.loads(json_str)
        target_dt = datetime.strptime(target_date_str, "%Y-%m-%d").date()
        
        selected_row = None
        prev_row = None
        
        # 遍历 K 线寻找目标日期或最接近的前一个交易日
        for i, row in enumerate(data):
            # 兼容不同接口的日期字段名 (day 或 d)
            row_date_raw = row.get('day') or row.get('d')
            row_dt = datetime.strptime(row_date_raw.split(' ')[0], "%Y-%m-%d").date()
            
            if row_dt <= target_dt:
                selected_row = row
                if i > 0: prev_row = data[i-1]
            else:
                break
        
        if selected_row:
            close_p = float(selected_row.get('close') or selected_row.get('c'))
            # 获取前一日收盘价用于计算涨跌幅
            ref_p = float(prev_row.get('close') or prev_row.get('c')) if prev_row else close_p
            change_p = ((close_p - ref_p) / ref_p * 100) if ref_p else 0
            
            actual_date = (selected_row.get('day') or selected_row.get('d')).split(' ')[0]
            note = f"收盘价: {close_p}"
            if actual_date != target_date_str:
                note = f"⚠️ 该日休市，显示最近交易日({actual_date})数据。"

            return {
                "currentPrice": round(close_p, 2),
                "changePercent": round(change_p, 2),
                "historicalNote": note
            }
    except Exception as e:
        print(f"Error fetching {sina_code}: {e}")
    return None

# --- 4. 实时行情抓取 ---
def fetch_live_data():
    codes = ",".join([s['sina_code'] for s in STOCKS_CONFIG if s['sina_code']])
    results = {}
    try:
        url = f"http://hq.sinajs.cn/list={codes}"
        resp = requests.get(url, headers={"Referer": "http://finance.sina.com.cn/"}, timeout=5)
        content = resp.content.decode('gbk')
        for line in content.splitlines():
            if "=" not in line: continue
            code = line.split('=')[0].split('_str_')[-1]
            data = line.split('=')[1].strip('";').split(',')
            if len(data) < 10: continue
            
            # 美股/港股/A股 新浪返回的格式索引不同
            if code.startswith('gb_'): # 美股
                p, cp = float(data[1]), float(data[2])
            elif code.startswith('rt_hk'): # 港股
                p, cp = float(data[6]), float(data[8])
            else: # A 股
                p, prev = float(data[3]), float(data[2])
                cp = (p - prev) / prev * 100 if prev else 0
            
            results[code] = {"currentPrice": round(p, 2), "changePercent": round(cp, 2)}
    except: pass
    return results

# --- 5. API 路由 ---

@app.get("/")
def home():
    return {"status": "online", "engine": "Sina Finance Regex", "version": APP_VERSION}

@app.get("/api/stocks")
def get_stocks_api(date: str = Query(None)):
    """
    根据参数切换模式。
    如果带 ?date=YYYY-MM-DD，进入新浪历史回溯模式。
    否则返回实时行情。
    """
    final_list = []
    
    if date:
        # 历史复盘模式：使用线程池加速多股票抓取
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
            if h_data:
                item.update(h_data)
            else:
                item.update({"currentPrice": "-", "changePercent": 0, "error": True})
            final_list.append(item)
    else:
        # 实时监听模式
        live_data = fetch_live_data()
        for s in STOCKS_CONFIG:
            item = {**s}
            l_data = live_data.get(s['sina_code'])
            if l_data:
                item.update(l_data)
            else:
                item.update({"currentPrice": "-", "changePercent": 0, "error": True})
            # 注入新闻
            item["news"] = NEWS_CACHE.get(s["id"], {"title": "正在获取最新热点...", "link": "#"})
            final_list.append(item)
            
    return final_list

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)