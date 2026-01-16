from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import requests
import yfinance as yf
import threading
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import random
import json

app = FastAPI()

# 版本标识
APP_VERSION = "2026.01.15.SINA_HIST" 

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. 股票配置池 ---
STOCKS_CONFIG = [
    # US
    {"id": "NVDA", "sina_code": "gb_nvda", "ticker": "NVDA", "name": "英伟达", "market": "US", "sector": "hardware", "subSector": "GPU 芯片", "query": "NVIDIA stock news"},
    {"id": "AMD", "sina_code": "gb_amd", "ticker": "AMD", "name": "超微半导体", "market": "US", "sector": "hardware", "subSector": "GPU 芯片", "query": "AMD stock news"},
    {"id": "AVGO", "sina_code": "gb_avgo", "ticker": "AVGO", "name": "博通", "market": "US", "sector": "hardware", "subSector": "网络/ASIC", "query": "Broadcom news"},
    {"id": "MU", "sina_code": "gb_mu", "ticker": "MU", "name": "镁光科技", "market": "US", "sector": "hardware", "subSector": "HBM 存储", "query": "Micron news"},
    {"id": "TSM_US", "sina_code": "gb_tsm", "ticker": "TSM", "name": "台积电(ADR)", "market": "US", "sector": "hardware", "subSector": "晶圆代工", "query": "TSMC news"},
    {"id": "SMCI", "sina_code": "gb_smci", "ticker": "SMCI", "name": "超微电脑", "market": "US", "sector": "hardware", "subSector": "AI 服务器", "query": "Super Micro news"},
    {"id": "TSLA", "sina_code": "gb_tsla", "ticker": "TSLA", "name": "特斯拉", "market": "US", "sector": "hardware", "subSector": "机器人/Dojo", "query": "Tesla AI news"},
    {"id": "MSFT", "sina_code": "gb_msft", "ticker": "MSFT", "name": "微软", "market": "US", "sector": "application", "subSector": "云/模型", "query": "Microsoft AI"},
    {"id": "GOOGL", "sina_code": "gb_googl", "ticker": "GOOGL", "name": "谷歌", "market": "US", "sector": "application", "subSector": "搜索/模型", "query": "Google Gemini"},
    {"id": "META", "sina_code": "gb_meta", "ticker": "META", "name": "Meta", "market": "US", "sector": "application", "subSector": "社交/模型", "query": "Meta Llama"},
    {"id": "PLTR", "sina_code": "gb_pltr", "ticker": "PLTR", "name": "Palantir", "market": "US", "sector": "application", "subSector": "数据分析", "query": "Palantir AI"},
    # CN
    {"id": "601138", "sina_code": "sh601138", "ticker": "601138.SS", "name": "工业富联", "market": "CN", "sector": "hardware", "subSector": "AI 服务器", "query": "工业富联 新闻"},
    {"id": "300308", "sina_code": "sz300308", "ticker": "300308.SZ", "name": "中际旭创", "market": "CN", "sector": "hardware", "subSector": "光模块", "query": "中际旭创 新闻"},
    {"id": "688041", "sina_code": "sh688041", "ticker": "688041.SS", "name": "海光信息", "market": "CN", "sector": "hardware", "subSector": "AI 芯片", "query": "海光信息 新闻"},
    {"id": "688256", "sina_code": "sh688256", "ticker": "688256.SS", "name": "寒武纪", "market": "CN", "sector": "hardware", "subSector": "AI 芯片", "query": "寒武纪 新闻"},
    # HK
    {"id": "0981", "sina_code": "rt_hk00981", "ticker": "0981.HK", "name": "中芯国际", "market": "HK", "sector": "hardware", "subSector": "晶圆代工", "query": "中芯国际 新闻"},
    {"id": "0700", "sina_code": "rt_hk00700", "ticker": "0700.HK", "name": "腾讯控股", "market": "HK", "sector": "application", "subSector": "社交/游戏", "query": "腾讯 混元"},
    {"id": "09988", "sina_code": "rt_hk09988", "ticker": "9988.HK", "name": "阿里巴巴", "market": "HK", "sector": "application", "subSector": "云/电商", "query": "阿里巴巴 阿里云"},
]

NEWS_CACHE = {}

# --- 新浪财经 K 线接口封装 (历史数据) ---
def fetch_sina_historical_single(sina_code, target_date_str):
    """从新浪获取历史收盘数据"""
    try:
        # A 股接口
        if sina_code.startswith(('sh', 'sz')):
            url = f"http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={sina_code}&scale=240&ma=no&datalen=20"
        # 港股接口
        elif sina_code.startswith('rt_hk'):
            symbol = sina_code.replace('rt_hk', '')
            url = f"http://quotes.sina.cn/hk/api/jsonp_v2.php/var%20_code=/HK_StockService.getHKDayKLine?symbol={symbol}"
        # 美股接口
        elif sina_code.startswith('gb_'):
            symbol = sina_code.replace('gb_', '').upper()
            url = f"http://stock.finance.sina.com.cn/usstock/api/jsonp.php/IO.StockService.getKLineData?symbol={symbol}&type=day"
        else:
            return None

        resp = requests.get(url, timeout=5)
        # 简单清洗数据 (新浪返回的 JSON 往往是不规范的或带 JS 变量名)
        content = resp.text
        if "[" not in content: return None
        json_str = content[content.find("["):content.rfind("]")+1]
        data = json.loads(json_str)

        # 寻找目标日期或最接近的前一个交易日
        target_dt = datetime.strptime(target_date_str, "%Y-%m-%d").date()
        
        selected_row = None
        prev_row = None
        
        for i, row in enumerate(data):
            # 新浪的时间格式不一，需要兼容
            row_date_str = row.get('day') or row.get('d')
            row_dt = datetime.strptime(row_date_str.split(' ')[0], "%Y-%m-%d").date()
            
            if row_dt <= target_dt:
                selected_row = row
                # 为了计算涨跌幅，我们需要获取上一行
                if i > 0:
                    prev_row = data[i-1]
            else:
                break
        
        if selected_row:
            close_p = float(selected_row.get('close') or selected_row.get('c'))
            open_p = float(selected_row.get('open') or selected_row.get('o'))
            # 优先用前一日收盘计算涨幅，如果没有则用当日开盘
            ref_p = float(prev_row.get('close') or prev_row.get('c')) if prev_row else open_p
            change_p = ((close_p - ref_p) / ref_p * 100) if ref_p else 0
            
            actual_date = selected_row.get('day') or selected_row.get('d')
            note = f"收盘价: {close_p}"
            if actual_date.split(' ')[0] != target_date_str:
                note = f"⚠️ 选定日休市，显示最近交易日({actual_date.split(' ')[0]})收盘价: {close_p}"

            return {
                "currentPrice": round(close_p, 2),
                "changePercent": round(change_p, 2),
                "historicalNote": note
            }
    except:
        pass
    return None

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
    return results

@app.get("/")
def read_root():
    return {"status": "online", "version": APP_VERSION}

@app.get("/api/stocks")
def get_stocks(date: str = Query(None)):
    final_list = []
    
    if date:
        # --- 历史模式：多线程调用新浪 K 线 ---
        threads = []
        results = {}

        def worker(stock):
            res = fetch_sina_historical_single(stock['sina_code'], date)
            if res: results[stock['id']] = res

        for stock in STOCKS_CONFIG:
            t = threading.Thread(target=worker, args=(stock,))
            threads.append(t)
            t.start()
        
        for t in threads: t.join()

        for stock in STOCKS_CONFIG:
            item = {**stock}
            m_data = results.get(stock['id'])
            if m_data: item.update(m_data)
            else: item.update({"currentPrice": "-", "changePercent": 0, "error": True})
            final_list.append(item)
    else:
        # --- 实时模式 ---
        live_data = fetch_live_data()
        for stock in STOCKS_CONFIG:
            item = {**stock}
            m_data = live_data.get(stock['sina_code'])
            if m_data: item.update(m_data)
            else: item.update({"currentPrice": "-", "changePercent": 0, "error": True})
            final_list.append(item)
            
    return final_list