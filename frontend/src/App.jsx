import React, { useState, useEffect, useMemo } from 'react';
import { Monitor, Cpu, TrendingUp, TrendingDown, Globe, Activity, RefreshCw, Smartphone, Zap, Server, Loader, AlertCircle, Info, ExternalLink, Newspaper } from 'lucide-react';

// --- 配置 API 地址 ---
// 智能判断：如果是本地开发(localhost)，使用本地后端；如果是云端部署，使用环境变量 VITE_API_URL
// 如果没有设置环境变量，默认为本地地址
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

// 样式组件
const Card = ({ children, className = "" }) => (
  <div className={`bg-gray-800 rounded-xl border border-gray-700 shadow-lg ${className}`}>
    {children}
  </div>
);

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

// 股票表格组件
const StockTable = ({ stocks, type }) => {
  const isHardware = type === 'hardware';
  const themeColor = isHardware ? 'text-cyan-400' : 'text-orange-400';
  const themeBg = isHardware ? 'bg-cyan-900/30' : 'bg-orange-900/30';
  const themeBorder = isHardware ? 'border-cyan-700' : 'border-orange-700';

  return (
    <div className="mb-8 animate-fade-in">
      {/* 分类标题 */}
      <div className="flex items-center gap-3 mb-4 pl-1">
        <div className={`p-2 rounded-lg ${themeBg} ${themeColor} border ${themeBorder} shadow-sm`}>
          {isHardware ? <Server size={20} /> : <Zap size={20} />}
        </div>
        <div>
          <h2 className="text-xl font-bold text-gray-100 flex items-center gap-2">
            {isHardware ? 'AI 硬件端' : 'AI 应用端'}
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
                <th className="px-6 py-4 w-28 text-right">最新价</th>
                <th className="px-6 py-4 w-28 text-right">涨跌额</th>
                <th className="px-6 py-4 w-28 text-right">涨跌幅</th>
                <th className="px-6 py-4">Google News 实时热点</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700">
              {(!stocks || stocks.length === 0) ? (
                 <tr><td colSpan="7" className="px-6 py-8 text-center text-gray-500">正在同步数据...</td></tr>
              ) : (
                stocks.map((stock) => (
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
                            {stock.error ? <span className="text-red-500 text-xs">暂无</span> : stock.currentPrice}
                        </div>
                    </td>
                    <td className={`px-6 py-4 text-right font-mono ${stock.changeAmount >= 0 ? 'text-red-400' : 'text-green-400'}`}>
                        {stock.changeAmount > 0 ? '+' : ''}{parseFloat(stock.changeAmount || 0).toFixed(2)}
                    </td>
                    <td className="px-6 py-4 text-right">
                        {stock.error ? (
                            <span className="text-gray-600">-</span>
                        ) : (
                            <div className={`font-mono font-bold ${stock.changePercent >= 0 ? 'text-red-400' : 'text-green-400'}`}>
                            {stock.changePercent >= 0 ? '+' : ''}{stock.changePercent?.toFixed(2)}%
                            </div>
                        )}
                    </td>
                    {/* 新闻展示区域 */}
                    <td className="px-6 py-4 align-top">
                        {stock.news && stock.news.title !== "正在获取最新资讯..." ? (
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
                                正在抓取新闻...
                            </div>
                        )}
                    </td>
                    </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};


export default function AIMarketTracker() {
  const [stocks, setStocks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('ALL'); 
  const [lastUpdated, setLastUpdated] = useState(null);

  // --- 核心：从后端获取真实数据 ---
  const fetchStockData = async () => {
    // 首次加载显示 Loading，后续静默更新
    if (stocks.length === 0) setLoading(true);
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000); // 云端可能稍慢，给15秒

    try {
      // 使用动态配置的 API 地址
      const response = await fetch(`${API_BASE_URL}/api/stocks`, {
        signal: controller.signal
      });
      clearTimeout(timeoutId);

      if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
      
      const data = await response.json();
      
      if (Array.isArray(data)) {
        setStocks(data);
        setLastUpdated(new Date());
        setError(null);
      } else {
        throw new Error("无效的数据格式");
      }
    } catch (err) {
      console.error("Fetch error:", err);
      if (stocks.length === 0) {
          setError(`连接失败: ${err.message}。请检查后端服务是否正常。`);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStockData();
    // 30秒刷新一次数据
    const intervalId = setInterval(fetchStockData, 30000); 
    return () => clearInterval(intervalId);
  }, []);

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

  const stocksInMarket = activeTab === 'ALL' 
    ? stocks 
    : stocks.filter(s => s.market === activeTab);
  
  const hardwareStocks = stocksInMarket.filter(s => s.sector === 'hardware');
  const applicationStocks = stocksInMarket.filter(s => s.sector === 'application');

  const getSentiment = () => {
    if (loading && stocks.length === 0) return "正在从新浪财经同步数据...";
    if (error) return "数据源连接中断。";
    
    const hChange = parseFloat(marketStats.hardware.change);
    const aChange = parseFloat(marketStats.application.change);
    
    if (hChange > 0.5 && aChange > 0.5) return "🔥 情绪高涨：今日资金全面流入 AI 板块。";
    if (hChange < -0.5 && aChange < -0.5) return "❄️ 避险情绪：受宏观影响，AI 产业链普遍回调。";
    if (hChange > 0.5) return "⚙️ 硬强软弱：资金聚焦算力基建，应用端相对疲软。";
    if (aChange > 0.5) return "📱 软强硬弱：硬件端获利了结，资金切换至应用股。";
    return "⚖️ 窄幅震荡：市场缺乏明确方向。";
  };

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 font-sans p-4 md:p-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-center mb-8 gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold flex items-center gap-3 text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
            <Globe className="w-8 h-8 text-blue-400" />
            全球 AI 股市追踪
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            实时追踪 US / CN / HK / TW 四大市场 AI 产业链 (Sina Finance + Google News)
          </p>
        </div>
        
        <div className="flex items-center gap-3">
            {error ? (
                <div className="flex items-center gap-2 text-red-400 text-sm border border-red-800 px-3 py-1 rounded-full bg-red-900/20">
                    <AlertCircle className="w-4 h-4"/> {error}
                </div>
            ) : (
                <div className="flex items-center gap-3 bg-gray-800 px-4 py-2 rounded-full border border-gray-700">
                    <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                    <span className="text-xs text-gray-400 font-mono">
                        {lastUpdated ? lastUpdated.toLocaleTimeString() : '--:--:--'}
                    </span>
                    <button onClick={() => {fetchStockData();}} className="hover:text-white transition-colors" title="刷新">
                        <RefreshCw className={`w-3 h-3 text-gray-500 ${loading ? 'animate-spin' : ''}`} />
                    </button>
                </div>
            )}
        </div>
      </div>

      {/* 市场概览卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <Card className="p-5 relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
            <Cpu size={80} />
          </div>
          <div className="flex items-center gap-2 mb-2">
            <Cpu className="text-cyan-400 w-5 h-5" />
            <h3 className="text-gray-400 font-medium">AI 硬件/基建指数</h3>
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
            <h3 className="text-gray-400 font-medium">AI 应用/软件指数</h3>
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

        <Card className="p-5 bg-gradient-to-br from-indigo-900 to-gray-800 border-indigo-700">
          <div className="flex items-center gap-2 mb-3">
            <Activity className="text-indigo-400 w-5 h-5" />
            <h3 className="text-indigo-200 font-medium">AI 市场风向标</h3>
          </div>
          <p className="text-gray-300 text-sm leading-relaxed mb-4">
            {getSentiment()}
          </p>
          <div className="flex gap-2">
            <div className="bg-black/30 px-3 py-1 rounded text-xs text-gray-400">
              数据源: <span className="text-white">新浪财经</span>
            </div>
            <div className="bg-black/30 px-3 py-1 rounded text-xs text-gray-400">
              状态: <span className="text-green-400">● 实时同步</span>
            </div>
          </div>
        </Card>
      </div>

      {/* 市场筛选 Tab */}
      <div className="flex flex-col gap-4">
        <div className="flex gap-2 overflow-x-auto pb-2 border-b border-gray-700 mb-4">
          {['ALL', 'US', 'CN', 'HK', 'TW'].map(market => (
            <button
              key={market}
              onClick={() => setActiveTab(market)}
              className={`px-6 py-3 rounded-t-lg font-medium transition-all whitespace-nowrap relative top-[1px] ${
                activeTab === market 
                ? 'bg-gray-800 text-blue-400 border-t border-l border-r border-gray-700' 
                : 'text-gray-400 hover:text-white'
              }`}
            >
              {market === 'ALL' ? '全球概览' : 
               market === 'US' ? '🇺🇸 美股' :
               market === 'CN' ? '🇨🇳 A股' :
               market === 'HK' ? '🇭🇰 港股' : '🇹🇼 台股'}
            </button>
          ))}
        </div>

        {/* 股票列表区域 */}
        {loading && stocks.length === 0 ? (
            <div className="flex justify-center items-center py-20">
                <Loader className="w-10 h-10 text-blue-500 animate-spin" />
            </div>
        ) : (
            <div className="animate-fade-in">
                <StockTable stocks={hardwareStocks} type="hardware" />
                {/* 台湾板块特例：仅展示硬件 */}
                {activeTab !== 'TW' && <StockTable stocks={applicationStocks} type="application" />}
            </div>
        )}
        
      </div>
      
      <div className="mt-8 text-center text-gray-600 text-sm pb-8">
        <p>© 2026 AI Market Tracker | Power by Sina Finance & Google News</p>
      </div>
    </div>
  );
}