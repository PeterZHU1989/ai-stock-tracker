import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { Monitor, Cpu, TrendingUp, TrendingDown, Globe, Activity, RefreshCw, Smartphone, Zap, Server, Loader, AlertCircle, Newspaper, ExternalLink, Calendar, History, Play } from 'lucide-react';

/**
 * --- API 地址配置 ---
 * 确保在 Vercel 生产环境下使用环境变量，本地开发则回退到 localhost
 */
const getApiBaseUrl = () => {
  try {
    // @ts-ignore
    let envUrl = import.meta.env ? import.meta.env.VITE_API_URL : null;
    if (envUrl && envUrl.endsWith('/')) envUrl = envUrl.slice(0, -1);
    return envUrl || 'http://127.0.0.1:8000';
  } catch (e) {
    return 'http://127.0.0.1:8000';
  }
};

const API_BASE_URL = getApiBaseUrl();

// 样式组件：标签
const Badge = ({ children, type }) => {
  const colors = {
    US: "bg-blue-900 text-blue-200 border-blue-700",
    CN: "bg-red-900 text-red-200 border-red-700",
    HK: "bg-purple-900 text-purple-200 border-purple-700",
    hardware: "bg-cyan-900 text-cyan-200 border-cyan-700",
    application: "bg-orange-900 text-orange-200 border-orange-700"
  };
  return <span className={`px-2 py-0.5 text-xs font-medium rounded border ${colors[type] || "bg-gray-700"}`}>{children}</span>;
};

// 股票数据表格组件
const StockTable = ({ stocks, type, isHistorical }) => {
  if (!stocks || stocks.length === 0) return null;
  const isHardware = type === 'hardware';

  return (
    <div className="mb-8 animate-fade-in">
      <div className="flex items-center gap-3 mb-4 pl-1">
        <div className={`p-2 rounded-lg ${isHardware ? 'bg-cyan-900/30 text-cyan-400 border-cyan-700' : 'bg-orange-900/30 text-orange-400 border-orange-700'} border shadow-sm`}>
          {isHardware ? <Server size={20} /> : <Zap size={20} />}
        </div>
        <h2 className="text-xl font-bold text-gray-100">{isHardware ? 'AI 硬件端龙头' : 'AI 应用端核心'}</h2>
      </div>
      <div className="bg-gray-800 rounded-xl border border-gray-700 shadow-lg overflow-hidden overflow-x-auto">
        <table className="w-full text-left text-sm text-gray-400">
          <thead className="bg-gray-900/50 text-gray-300 uppercase font-medium">
            <tr>
              <th className="px-6 py-4 w-32">代码/名称</th>
              <th className="px-6 py-4 w-24">市场</th>
              <th className="px-6 py-4 w-32">赛道细分</th>
              <th className="px-6 py-4 w-28 text-right">{isHistorical ? '当日收盘' : '最新价'}</th>
              <th className="px-6 py-4 w-28 text-right">当日涨跌</th>
              <th className="px-6 py-4">{isHistorical ? '数据状态' : 'Google News 实时热点'}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {stocks.map((stock) => (
              <tr key={stock.id} className="hover:bg-gray-750 transition-colors group">
                <td className="px-6 py-4">
                  <div className="flex flex-col">
                    <span className="text-white font-bold">{stock.name}</span>
                    <span className="text-xs font-mono text-gray-500">{stock.ticker}</span>
                  </div>
                </td>
                <td className="px-6 py-4"><Badge type={stock.market}>{stock.market}</Badge></td>
                <td className="px-6 py-4"><span className="text-xs text-gray-300 bg-gray-700/50 px-2 py-1 rounded border border-gray-600">{stock.subSector}</span></td>
                <td className="px-6 py-4 text-right font-mono text-white font-medium">
                    {stock.error ? <span className="text-red-500 text-xs">缺失</span> : stock.currentPrice}
                </td>
                <td className={`px-6 py-4 text-right font-mono font-bold ${stock.changePercent >= 0 ? 'text-red-400' : 'text-green-400'}`}>
                  {stock.changePercent >= 0 ? '+' : ''}{stock.changePercent.toFixed(2)}%
                </td>
                <td className="px-6 py-4 align-top">
                  {isHistorical ? (
                    <div className="text-xs text-gray-400 italic leading-relaxed">
                      {stock.historicalNote || (stock.error ? "当日无有效交易记录。" : "数据同步自新浪财经。")}
                    </div>
                  ) : (
                    stock.news && stock.news.link !== "#" ? (
                      <a href={stock.news.link} target="_blank" rel="noopener noreferrer" className="flex items-start gap-2 p-2 rounded bg-gray-700/30 border border-gray-700/50 hover:bg-gray-700 hover:border-blue-500/50 transition-all group/news">
                        <Newspaper size={14} className="text-blue-400 mt-0.5 flex-shrink-0 group-hover/news:text-blue-300" />
                        <div>
                          <span className="text-xs text-gray-200 font-medium line-clamp-2 hover:underline">{stock.news.title}</span>
                          <div className="flex items-center gap-1 mt-1 text-[10px] text-gray-500">Google News <ExternalLink size={8} /></div>
                        </div>
                      </a>
                    ) : (
                      <div className="flex items-center gap-2 text-xs text-gray-600 italic"><Loader size={12} className="animate-spin" />同步中...</div>
                    )
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default function App() {
  const [stocks, setStocks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('ALL');
  const [selectedDate, setSelectedDate] = useState("");
  const [lastUpdated, setLastUpdated] = useState(null);
  const dateInputRef = useRef(null);

  // 派生状态：是否处于历史模式
  const isHistoricalMode = useMemo(() => selectedDate !== "", [selectedDate]);

  // 核心数据获取逻辑
  const fetchStockData = useCallback(async (targetDate = "") => {
    // 关键点：如果是回溯模式，发起请求前立即清空旧列表，防止数据显示冲突
    if (targetDate !== "") {
        setStocks([]);
        setLoading(true);
    } else if (stocks.length === 0) {
        setLoading(true);
    }
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000); 

    try {
      const url = targetDate ? `${API_BASE_URL}/api/stocks?date=${targetDate}` : `${API_BASE_URL}/api/stocks`;
      const response = await fetch(url, { signal: controller.signal });
      
      if (!response.ok) {
         const errBody = await response.json().catch(() => ({}));
         throw new Error(errBody.detail || `服务器返回错误 (${response.status})`);
      }

      const data = await response.json();
      
      if (Array.isArray(data)) {
        setStocks(data);
        setLastUpdated(new Date());
        setError(null);
      } else {
        throw new Error("返回的数据格式不符合预期");
      }
    } catch (err) {
      console.error("Fetch Error:", err);
      if (targetDate) {
        setError(`未找到 ${targetDate} 的有效数据。可能该日为非交易日、数据尚未同步或后端接口异常。`);
        setStocks([]); 
      } else if (stocks.length === 0) {
        setError("连接后端服务失败，请检查后端运行状态及网络连接。");
      }
    } finally {
      setLoading(false);
      clearTimeout(timeoutId);
    }
  }, [stocks.length]);

  // 模式与刷新控制
  useEffect(() => {
    document.title = "ai-stock-tracker";
    
    if (isHistoricalMode) {
      // 历史模式：执行抓取逻辑，并确保清理掉所有定时刷新
      fetchStockData(selectedDate);
      return () => {}; 
    } else {
      // 实时模式：执行初始抓取并启动 30 秒轮询定时器
      fetchStockData();
      const intervalId = setInterval(() => fetchStockData(), 30000);
      // 清理函数：确保在选择日期或组件卸载时物理停止定时器
      return () => clearInterval(intervalId);
    }
  }, [selectedDate, isHistoricalMode, fetchStockData]);

  // 计算板块指数
  const marketStats = useMemo(() => {
    const calc = (filterFn) => {
      const f = stocks.filter(filterFn).filter(s => !s.error);
      if (f.length === 0) return { val: 1000, change: 0 };
      const totalChange = f.reduce((acc, s) => acc + (s.changePercent || 0), 0);
      const avg = totalChange / f.length;
      return { val: (1000 * (1 + avg/100)).toFixed(1), change: avg.toFixed(2) };
    };
    return { hardware: calc(s => s.sector === 'hardware'), application: calc(s => s.sector === 'application') };
  }, [stocks]);

  const hardwareStocks = stocks.filter(s => s.sector === 'hardware' && (activeTab === 'ALL' || s.market === activeTab));
  const applicationStocks = stocks.filter(s => s.sector === 'application' && (activeTab === 'ALL' || s.market === activeTab));

  const getSentiment = () => {
    if (loading && stocks.length === 0) return "同步市场快照中...";
    if (error) return "数据获取遇到障碍";

    const prefix = isHistoricalMode ? `📅 ${selectedDate} 复盘：` : "🚀 实时播报：";
    const hChange = parseFloat(marketStats.hardware.change);
    const aChange = parseFloat(marketStats.application.change);
    
    let analysis = "";
    if (hChange > 0.5 && aChange > 0.5) analysis = "多头火热，全线爆发。";
    else if (hChange < -0.5 && aChange < -0.5) analysis = "避险浓厚，集体回调。";
    else if (hChange > 0.5) analysis = "硬强软弱，资金聚焦算力。";
    else if (aChange > 0.5) analysis = "软强硬弱，应用端反弹。";
    else analysis = "窄幅震荡博弈中。";

    return `${prefix}${analysis}`;
  };

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 font-sans p-4 md:p-8">
      {/* Header 工具栏 */}
      <div className="flex flex-col md:flex-row justify-between items-center mb-6 gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold flex items-center gap-3 text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
            <Globe className="text-blue-400" /> AI 股市追踪系统
          </h1>
          <p className="text-gray-400 text-sm mt-1">{isHistoricalMode ? `正在回溯历史: ${selectedDate}` : '全球 AI 产业链核心个股实时监控'}</p>
        </div>
        
        <div className="flex items-center gap-3">
          {/* 交互日期选择器 */}
          <div className="flex items-center gap-2 bg-gray-800 p-1 rounded-lg border border-gray-700 cursor-pointer hover:border-blue-500/50 transition-all group" onClick={() => dateInputRef.current?.showPicker()}>
            <Calendar size={14} className="ml-2 text-blue-400 group-hover:scale-110 transition-transform" />
            <input ref={dateInputRef} type="date" value={selectedDate} onChange={(e) => setSelectedDate(e.target.value)} max={new Date().toISOString().split("T")[0]} className="bg-gray-900 text-gray-200 text-xs p-1.5 rounded focus:outline-none cursor-pointer" onClick={(e) => e.stopPropagation()} />
            {isHistoricalMode && <button onClick={(e) => { e.stopPropagation(); setSelectedDate(""); }} className="bg-blue-600 hover:bg-blue-500 px-3 py-1.5 text-xs rounded shadow-lg transition-colors">切回实时</button>}
          </div>

          <div className="bg-gray-800 px-4 py-2 rounded-full border border-gray-700 flex items-center gap-3 shadow-inner">
            <div className={`w-2 h-2 rounded-full ${isHistoricalMode ? 'bg-amber-500 shadow-[0_0_8px_#f59e0b]' : 'bg-green-500 animate-pulse'}`}></div>
            <span className="text-xs font-mono text-gray-400">{isHistoricalMode ? 'HISTORY' : (lastUpdated ? lastUpdated.toLocaleTimeString() : '--:--:--')}</span>
            {!isHistoricalMode && <button onClick={() => fetchStockData()} className="hover:text-white transition-colors"><RefreshCw className={`w-3.5 h-3.5 text-gray-500 ${loading ? 'animate-spin' : ''}`} /></button>}
          </div>
        </div>
      </div>

      {/* 错误提示条：增强交互，允许快速恢复 */}
      {error && isHistoricalMode && (
          <div className="mb-6 bg-red-900/20 border border-red-800/40 p-4 rounded-xl text-red-400 text-sm flex items-center gap-3 animate-pulse">
              <AlertCircle size={18} className="flex-shrink-0" />
              <span>{error}</span>
              <button onClick={() => setSelectedDate("")} className="ml-auto bg-red-500/20 px-3 py-1 rounded border border-red-500/50 hover:bg-red-500/40 transition-all font-medium whitespace-nowrap">重试实时模式</button>
          </div>
      )}

      {/* 历史复盘提示卡 */}
      {isHistoricalMode && !error && (
        <div className="mb-6 bg-amber-900/20 border border-amber-800/40 p-4 rounded-xl text-amber-200 text-sm flex items-center gap-3 animate-fade-in shadow-xl">
          <History className="text-amber-500 flex-shrink-0" />
          <span>您正处于<strong>新浪财经 K 线回溯模式</strong>。当前显示为所选日期的收盘数据快照。</span>
        </div>
      )}

      {/* 核心看板 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-gray-800 p-5 rounded-xl border border-gray-700 relative overflow-hidden group">
          <div className="absolute -right-4 -bottom-4 opacity-5 group-hover:opacity-10 transition-opacity"><Cpu size={120} /></div>
          <div className="text-gray-400 text-sm mb-1 flex items-center gap-2"><Cpu size={14} className="text-cyan-400" />硬件指数</div>
          <div className="flex items-baseline gap-3 relative z-10">
            <span className="text-3xl font-bold">{marketStats.hardware.val}</span>
            <span className={`text-lg font-bold ${marketStats.hardware.change >= 0 ? 'text-red-400' : 'text-green-400'}`}>{marketStats.hardware.change >= 0 ? '↑' : '↓'}{marketStats.hardware.change}%</span>
          </div>
        </div>

        <div className="bg-gray-800 p-5 rounded-xl border border-gray-700 relative overflow-hidden group">
          <div className="absolute -right-4 -bottom-4 opacity-5 group-hover:opacity-10 transition-opacity"><Smartphone size={120} /></div>
          <div className="text-gray-400 text-sm mb-1 flex items-center gap-2"><Zap size={14} className="text-orange-400" />应用指数</div>
          <div className="flex items-baseline gap-3 relative z-10">
            <span className="text-3xl font-bold">{marketStats.application.val}</span>
            <span className={`text-lg font-bold ${marketStats.application.change >= 0 ? 'text-red-400' : 'text-green-400'}`}>{marketStats.application.change >= 0 ? '↑' : '↓'}{marketStats.application.change}%</span>
          </div>
        </div>

        <div className={`p-5 rounded-xl border border-gray-700 transition-all duration-500 bg-gradient-to-br shadow-lg ${isHistoricalMode ? 'from-amber-900/40 to-gray-800 border-amber-700/50' : 'from-indigo-900 to-gray-800 border-indigo-700/50'}`}>
          <div className="text-indigo-200 text-sm mb-2 font-medium flex items-center gap-2"><Activity size={16} />{isHistoricalMode ? '历史复盘总结' : '今日行情风向标'}</div>
          <p className="text-sm text-gray-200 leading-relaxed font-medium">{getSentiment()}</p>
          <div className="mt-3 flex gap-2">
            <span className="bg-black/30 px-2 py-0.5 rounded text-[10px] text-gray-400 uppercase">源: {isHistoricalMode ? 'SINA_KLINE' : 'SINA_LIVE'}</span>
            <span className={`bg-black/30 px-2 py-0.5 rounded text-[10px] uppercase font-bold ${isHistoricalMode ? 'text-amber-400' : 'text-green-400'}`}>{isHistoricalMode ? '● 历史' : '● 实时'}</span>
          </div>
        </div>
      </div>

      {/* 市场过滤选项 */}
      <div className="flex gap-2 mb-4 overflow-x-auto border-b border-gray-800 no-scrollbar">
        {['ALL', 'US', 'CN', 'HK'].map(m => (
          <button key={m} onClick={() => setActiveTab(m)} className={`px-6 py-3 font-medium transition-all relative top-[1px] ${activeTab === m ? 'border-b-2 border-blue-400 text-blue-400' : 'text-gray-500 hover:text-gray-300'}`}>{m === 'ALL' ? '全球概览' : m}</button>
        ))}
      </div>

      {/* 列表渲染容器 */}
      <div className="relative min-h-[400px]">
        {loading && (
          <div className="absolute inset-0 bg-gray-900/60 backdrop-blur-[2px] z-10 flex flex-col justify-center items-center rounded-xl animate-in fade-in duration-300">
            <Loader className="animate-spin text-blue-500 mb-2" size={36} />
            <span className="text-blue-400 text-sm font-medium tracking-widest">{isHistoricalMode ? `正在抓取 ${selectedDate} 行情...` : '正在刷新全球最新数据...'}</span>
          </div>
        )}
        <StockTable stocks={hardwareStocks} type="hardware" isHistorical={isHistoricalMode} />
        <StockTable stocks={applicationStocks} type="application" isHistorical={isHistoricalMode} />
      </div>
      
      <div className="mt-12 text-center text-gray-600 text-xs pb-8 border-t border-gray-800 pt-8">
        <p>© 2026 AI Market Tracker | Power by Sina Finance & Google News</p>
      </div>
    </div>
  );
}