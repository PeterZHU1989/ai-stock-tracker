import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { Monitor, Cpu, TrendingUp, TrendingDown, Globe, Activity, RefreshCw, Smartphone, Zap, Server, Loader, AlertCircle, Newspaper, ExternalLink, Calendar, History, Play } from 'lucide-react';

/**
 * --- API 地址配置 ---
 * 确保在 Vercel 环境下读取环境变量，在本地开发环境回退到 localhost。
 */
const getApiBaseUrl = () => {
  try {
    // @ts-ignore
    let envUrl = import.meta.env ? import.meta.env.VITE_API_URL : null;
    if (envUrl && envUrl.endsWith('/')) {
      envUrl = envUrl.slice(0, -1); // 移除末尾斜杠防止路径拼接错误
    }
    return envUrl || 'http://127.0.0.1:8000';
  } catch (e) {
    return 'http://127.0.0.1:8000';
  }
};

const API_BASE_URL = getApiBaseUrl();

// 样式组件：基础卡片容器
const Card = ({ children, className = "" }) => (
  <div className={`bg-gray-800 rounded-xl border border-gray-700 shadow-lg ${className}`}>
    {children}
  </div>
);

// 样式组件：市场/赛道标签
const Badge = ({ children, type }) => {
  const colors = {
    US: "bg-blue-900 text-blue-200 border-blue-700",
    CN: "bg-red-900 text-red-200 border-red-700",
    HK: "bg-purple-900 text-purple-200 border-purple-700",
    TW: "bg-green-900 text-green-200 border-green-700",
    hardware: "bg-cyan-900 text-cyan-200 border-cyan-700",
    application: "bg-orange-900 text-orange-200 border-orange-700"
  };
  return (
    <span className={`px-2 py-0.5 text-xs font-medium rounded border ${colors[type] || "bg-gray-700"}`}>
      {children}
    </span>
  );
};

// 股票数据表格组件
const StockTable = ({ stocks, type, isHistorical }) => {
  if (!stocks || stocks.length === 0) return null;

  const isHardware = type === 'hardware';
  const themeColor = isHardware ? 'text-cyan-400' : 'text-orange-400';
  const themeBg = isHardware ? 'bg-cyan-900/30' : 'bg-orange-900/30';
  const themeBorder = isHardware ? 'border-cyan-700' : 'border-orange-700';

  return (
    <div className="mb-8 animate-fade-in">
      {/* 分类标题栏 */}
      <div className="flex items-center gap-3 mb-4 pl-1">
        <div className={`p-2 rounded-lg ${themeBg} ${themeColor} border ${themeBorder} shadow-sm`}>
          {isHardware ? <Server size={20} /> : <Zap size={20} />}
        </div>
        <div>
          <h2 className="text-xl font-bold text-gray-100 flex items-center gap-2">
            {isHardware ? 'AI 硬件端龙头' : 'AI 应用与软件'}
          </h2>
          <p className="text-xs text-gray-500 font-medium mt-0.5">
            {isHardware ? 'Infrastructure: 芯片 / 算力 / 光通信 / PCB / 电源' : 'Applications: 模型 / 软件 / 互联网 / 终端'}
          </p>
        </div>
      </div>

      {/* 表格主体 */}
      <div className="bg-gray-800 rounded-xl border border-gray-700 shadow-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-gray-400">
            <thead className="bg-gray-900/50 text-gray-300 uppercase font-medium">
              <tr>
                <th className="px-6 py-4 w-32">代码/名称</th>
                <th className="px-6 py-4 w-24">市场</th>
                <th className="px-6 py-4 w-32">赛道细分</th>
                <th className="px-6 py-4 w-28 text-right">{isHistorical ? '收盘价' : '最新价'}</th>
                <th className="px-6 py-4 w-28 text-right">涨跌幅</th>
                <th className="px-6 py-4">{isHistorical ? '历史事件注记' : 'Google News 实时热点'}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700">
              {stocks.map((stock) => (
                <tr key={stock.id} className="hover:bg-gray-750 transition-colors group">
                  <td className="px-6 py-4">
                    <div className="flex flex-col">
                      <span className="text-white font-bold text-base">{stock.name}</span>
                      <span className="text-xs font-mono text-gray-500 group-hover:text-blue-400 transition-colors">{stock.ticker}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <Badge type={stock.market}>{stock.market}</Badge>
                  </td>
                  <td className="px-6 py-4">
                     <span className="text-xs text-gray-300 bg-gray-700/50 px-2 py-1 rounded border border-gray-600 whitespace-nowrap">
                        {stock.subSector}
                     </span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="font-mono text-white text-base font-medium tracking-tight">
                        {stock.error ? <span className="text-red-500 text-xs">Error</span> : stock.currentPrice}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right">
                    {stock.error ? (
                        <span className="text-gray-600">-</span>
                    ) : (
                        <div className={`font-mono font-bold ${stock.changePercent >= 0 ? 'text-red-400' : 'text-green-400'}`}>
                        {stock.changePercent >= 0 ? '+' : ''}{stock.changePercent.toFixed(2)}%
                        </div>
                    )}
                  </td>
                  <td className="px-6 py-4 align-top">
                    {isHistorical ? (
                        <div className="text-xs text-gray-400 leading-relaxed italic">
                            {stock.historicalNote || (stock.error ? "该日行情数据暂缺。" : "当日暂无特定宏观事件记录。")}
                        </div>
                    ) : (
                        stock.news && stock.news.link !== "#" ? (
                            <a 
                                href={stock.news.link} 
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="flex items-start gap-2 p-2 rounded bg-gray-700/30 border border-gray-700/50 hover:bg-gray-700 hover:border-blue-500/50 transition-all group/news"
                            >
                                <Newspaper size={14} className="text-blue-400 mt-0.5 flex-shrink-0 group-hover/news:text-blue-300" />
                                <div>
                                    <span className="text-xs text-gray-200 leading-relaxed font-medium line-clamp-2 hover:underline">
                                        {stock.news.title}
                                    </span>
                                    <div className="flex items-center gap-1 mt-1 text-[10px] text-gray-500">
                                        Google News <ExternalLink size={8} />
                                    </div>
                                </div>
                            </a>
                        ) : (
                            <div className="flex items-center gap-2 text-xs text-gray-600 italic">
                                <Loader size={12} className="animate-spin" />
                                同步资讯中...
                            </div>
                        )
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};


export default function App() {
  const [stocks, setStocks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('ALL'); 
  const [lastUpdated, setLastUpdated] = useState(null);
  
  // 历史回溯模式相关状态
  const [selectedDate, setSelectedDate] = useState("");
  const [isHistoricalMode, setIsHistoricalMode] = useState(false);

  // 使用 useCallback 封装获取逻辑，确保稳定性
  const fetchStockData = useCallback(async (targetDate = "") => {
    // 切换日期或初始化时显示 Loading
    if (stocks.length === 0 || targetDate !== "") setLoading(true);
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000); 

    try {
      const baseUrl = API_BASE_URL.replace(/\/$/, ""); // 确保末尾没有斜杠
      const queryParam = targetDate ? `?date=${targetDate}` : "";
      const url = `${baseUrl}/api/stocks${queryParam}`;

      const response = await fetch(url, { signal: controller.signal });
      if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
      const data = await response.json();
      
      if (Array.isArray(data)) {
        setStocks(data);
        setLastUpdated(new Date());
        setError(null);
        // 如果是带日期请求，进入历史模式
        setIsHistoricalMode(!!targetDate);
      } else {
        throw new Error("Invalid format");
      }
    } catch (err) {
      console.error("Fetch failed:", err);
      if (targetDate) {
          setError(`未找到 ${targetDate} 的有效交易记录。可能是休市日。`);
      } else if (stocks.length === 0) {
          setError(`连接后端失败，请确认后端已启动。`);
      }
    } finally {
      setLoading(false);
      clearTimeout(timeoutId);
    }
  }, [stocks.length]);

  // 副作用处理：负责初始化和定时刷新
  useEffect(() => {
    document.title = "ai-stock-tracker";
    
    // 如果没有选定日期（实时模式）
    if (!selectedDate) {
      fetchStockData();
      const intervalId = setInterval(() => fetchStockData(), 30000);
      return () => clearInterval(intervalId);
    } else {
      // 如果选定了日期，执行一次性抓取
      fetchStockData(selectedDate);
    }
  }, [selectedDate, fetchStockData]);

  // 计算板块指数
  const marketStats = useMemo(() => {
    const calculateIndex = (filterFn) => {
      const filtered = stocks.filter(filterFn).filter(s => !s.error);
      if (filtered.length === 0) return { val: 1000, change: 0 };
      const totalChange = filtered.reduce((acc, s) => acc + (s.changePercent || 0), 0);
      const avgChange = (totalChange / filtered.length).toFixed(2);
      const baseVal = 1000;
      const currentVal = (baseVal * (1 + avgChange/100)).toFixed(1);
      return { val: currentVal, change: avgChange };
    };

    return {
      hardware: calculateIndex(s => s.sector === 'hardware'),
      application: calculateIndex(s => s.sector === 'application'),
    };
  }, [stocks]);

  // 筛选列表
  const stocksInMarket = activeTab === 'ALL' 
    ? stocks 
    : stocks.filter(s => s.market === activeTab);
  
  const hardwareStocks = stocksInMarket.filter(s => s.sector === 'hardware');
  const applicationStocks = stocksInMarket.filter(s => s.sector === 'application');

  // 生成实时评价
  const getSentiment = () => {
    if (loading && stocks.length === 0) return "同步市场快照中...";
    if (error && isHistoricalMode) return error;
    if (error) return "数据源响应超时，请刷新重试。";

    const prefix = isHistoricalMode ? `📅 ${selectedDate} 回溯：` : "🚀 实时播报：";
    const hChange = parseFloat(marketStats.hardware.change);
    const aChange = parseFloat(marketStats.application.change);
    
    let analysis = "";
    if (hChange > 0.5 && aChange > 0.5) analysis = "多头占优，AI 产业链全线爆发。";
    else if (hChange < -0.5 && aChange < -0.5) analysis = "情绪低迷，板块出现普遍回调。";
    else if (hChange > 0.5) analysis = "硬强软弱，资金聚焦算力核心个股。";
    else if (aChange > 0.5) analysis = "软强硬弱，市场尝试挖掘应用端潜力。";
    else analysis = "震荡博弈，市场正寻找新的方向。";

    return `${prefix}${analysis}`;
  };

  const resetToLive = () => {
    setSelectedDate("");
    setIsHistoricalMode(false);
  };

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 font-sans p-4 md:p-8">
      {/* 顶部菜单栏 */}
      <div className="flex flex-col md:flex-row justify-between items-center mb-6 gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold flex items-center gap-3 text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
            <Globe className="w-8 h-8 text-blue-400" />
            AI 股市追踪系统
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            {isHistoricalMode ? `当前正在回溯历史交易日: ${selectedDate}` : '实时监控全球 AI 产业链核心标的'}
          </p>
        </div>
        
        <div className="flex flex-wrap items-center gap-3">
            {/* 日期选择器优化：点击容器即弹出原生日历 */}
            <div 
              className="flex items-center gap-2 bg-gray-800 p-1 rounded-lg border border-gray-700 shadow-sm hover:border-blue-500/50 transition-all cursor-pointer"
              onClick={(e) => {
                const input = e.currentTarget.querySelector('input');
                if (input && input.showPicker) input.showPicker();
              }}
            >
                <div className="flex items-center gap-2 px-3 text-gray-400 text-sm">
                    <Calendar size={14} className="text-blue-400" />
                    <span className="hidden sm:inline">日期回溯</span>
                </div>
                <input 
                    type="date" 
                    value={selectedDate}
                    onChange={(e) => setSelectedDate(e.target.value)}
                    max={new Date().toISOString().split("T")[0]}
                    className="bg-gray-900 text-gray-200 text-xs px-2 py-1.5 rounded border border-gray-700 focus:outline-none cursor-pointer"
                    onClick={(e) => e.stopPropagation()}
                />
                {isHistoricalMode && (
                    <button 
                        onClick={(e) => { e.stopPropagation(); resetToLive(); }}
                        className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs rounded transition-colors"
                    >
                        <Play size={10} fill="white" /> 实时
                    </button>
                )}
            </div>

            {/* 状态看板 */}
            <div className="flex items-center gap-3 bg-gray-800 px-4 py-2 rounded-full border border-gray-700 shadow-inner">
                <div className={`w-2 h-2 rounded-full ${isHistoricalMode ? 'bg-amber-500' : 'bg-green-500 animate-pulse'}`}></div>
                <span className="text-xs text-gray-400 font-mono">
                    {isHistoricalMode ? 'HISTORY' : (lastUpdated ? lastUpdated.toLocaleTimeString() : '--:--:--')}
                </span>
                {!isHistoricalMode && (
                    <button onClick={() => fetchStockData()} className="hover:text-white transition-colors">
                        <RefreshCw className={`w-3 h-3 text-gray-500 ${loading ? 'animate-spin' : ''}`} />
                    </button>
                )}
            </div>
        </div>
      </div>

      {/* 回溯模式特定提示栏 */}
      {isHistoricalMode && !error && (
        <div className="mb-6 flex items-center gap-3 bg-amber-900/20 border border-amber-800/40 p-4 rounded-xl text-amber-200 text-sm animate-fade-in shadow-lg">
            <History size={18} className="text-amber-500 flex-shrink-0" />
            <span>您正处于<strong>历史回溯模式</strong>。当前显示数据为该交易日最终收盘快照。</span>
        </div>
      )}

      {/* 指数中心 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <Card className="p-5 relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
            <Cpu size={80} />
          </div>
          <div className="flex items-center gap-2 mb-2">
            <Cpu className="text-cyan-400 w-5 h-5" />
            <h3 className="text-gray-400 font-medium">AI 硬件指数</h3>
          </div>
          <div className="flex items-baseline gap-3">
            <span className="text-3xl font-bold">{marketStats.hardware.val}</span>
            <span className={`text-lg font-medium flex items-center ${marketStats.hardware.change >= 0 ? 'text-red-400' : 'text-green-400'}`}>
              {marketStats.hardware.change >= 0 ? <TrendingUp size={18} className="mr-1"/> : <TrendingDown size={18} className="mr-1"/>}
              {marketStats.hardware.change}%
            </span>
          </div>
          <div className="mt-4 h-1 w-full bg-gray-700 rounded-full overflow-hidden">
            <div 
              className={`h-full ${marketStats.hardware.change >= 0 ? 'bg-red-500' : 'bg-green-500'}`} 
              style={{ width: `${Math.min(Math.abs(marketStats.hardware.change) * 20, 100)}%` }}
            ></div>
          </div>
        </Card>

        <Card className="p-5 relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
            <Smartphone size={80} />
          </div>
          <div className="flex items-center gap-2 mb-2">
            <Zap className="text-orange-400 w-5 h-5" />
            <h3 className="text-gray-400 font-medium">AI 应用指数</h3>
          </div>
          <div className="flex items-baseline gap-3">
            <span className="text-3xl font-bold">{marketStats.application.val}</span>
            <span className={`text-lg font-medium flex items-center ${marketStats.application.change >= 0 ? 'text-red-400' : 'text-green-400'}`}>
              {marketStats.application.change >= 0 ? <TrendingUp size={18} className="mr-1"/> : <TrendingDown size={18} className="mr-1"/>}
              {marketStats.application.change}%
            </span>
          </div>
          <div className="mt-4 h-1 w-full bg-gray-700 rounded-full overflow-hidden">
            <div 
              className={`h-full ${marketStats.application.change >= 0 ? 'bg-red-500' : 'bg-green-500'}`} 
              style={{ width: `${Math.min(Math.abs(marketStats.application.change) * 20, 100)}%` }}
            ></div>
          </div>
        </Card>

        <Card className={`p-5 bg-gradient-to-br border-gray-700 ${isHistoricalMode ? 'from-amber-900/40 to-gray-800' : 'from-indigo-900 to-gray-800'}`}>
          <div className="flex items-center gap-2 mb-3">
            <Activity className={isHistoricalMode ? 'text-amber-400 w-5 h-5' : 'text-indigo-400 w-5 h-5'} />
            <h3 className="text-indigo-200 font-medium">{isHistoricalMode ? '复盘分析' : '市场风向标'}</h3>
          </div>
          <p className="text-gray-300 text-sm leading-relaxed mb-4 font-medium">
            {getSentiment()}
          </p>
          <div className="flex gap-2">
            <div className="bg-black/30 px-3 py-1 rounded text-xs text-gray-400">
              数据源: <span className="text-white">{isHistoricalMode ? 'Yahoo' : 'Sina'} Finance</span>
            </div>
            <div className="bg-black/30 px-3 py-1 rounded text-xs text-gray-400">
              模式: <span className={isHistoricalMode ? 'text-amber-400' : 'text-green-400'}>{isHistoricalMode ? '● 历史复盘' : '● 实时监听'}</span>
            </div>
          </div>
        </Card>
      </div>

      <div className="flex flex-col gap-4">
        {/* 市场过滤选项 */}
        <div className="flex gap-2 overflow-x-auto pb-2 border-b border-gray-700 mb-4 no-scrollbar">
          {['ALL', 'US', 'CN', 'HK', 'TW'].map(market => (
            <button
              key={market}
              onClick={() => setActiveTab(market)}
              className={`px-6 py-3 rounded-t-lg font-medium transition-all whitespace-nowrap relative top-[1px] ${
                activeTab === market 
                ? 'bg-gray-800 text-blue-400 border-t border-l border-r border-gray-700' 
                : 'text-gray-400 hover:text-white hover:bg-gray-800/40'
              }`}
            >
              {market === 'ALL' ? '全球概览' : 
               market === 'US' ? '🇺🇸 美股' :
               market === 'CN' ? '🇨🇳 A股' :
               market === 'HK' ? '🇭🇰 港股' : '🇹🇼 台股'}
            </button>
          ))}
        </div>

        {/* 列表渲染容器 */}
        {loading && stocks.length === 0 ? (
            <div className="flex justify-center items-center py-20">
                <Loader className="w-10 h-10 text-blue-500 animate-spin" />
            </div>
        ) : (
            <div className="animate-fade-in relative">
                {/* 数据加载时的半透明遮罩 */}
                {loading && (
                    <div className="absolute inset-0 bg-gray-900/60 backdrop-blur-[1px] z-10 flex justify-center items-center rounded-xl">
                        <Loader className="w-8 h-8 text-blue-500 animate-spin" />
                    </div>
                )}
                <StockTable stocks={hardwareStocks} type="hardware" isHistorical={isHistoricalMode} />
                {activeTab !== 'TW' && <StockTable stocks={applicationStocks} type="application" isHistorical={isHistoricalMode} />}
            </div>
        )}
      </div>
      
      <div className="mt-8 text-center text-gray-600 text-sm pb-8">
        <p>© 2026 AI Market Tracker | Power by Global Data Engines</p>
      </div>
    </div>
  );
}