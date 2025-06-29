import { StockData, ChartData } from '../types/stock';

export const generateMockStockData = (): StockData[] => {
  const nifty100Stocks = [
    { symbol: 'HDFCBANK', name: 'HDFC Bank Ltd' },
    { symbol: 'INFY', name: 'Infosys Ltd' },
    { symbol: 'TCS', name: 'Tata Consultancy Services' },
    { symbol: 'RELIANCE', name: 'Reliance Industries Ltd' },
    { symbol: 'ICICIBANK', name: 'ICICI Bank Ltd' },
    { symbol: 'WIPRO', name: 'Wipro Ltd' },
    { symbol: 'SBIN', name: 'State Bank of India' },
    { symbol: 'ADANIPORTS', name: 'Adani Ports & SEZ Ltd' },
    { symbol: 'ASIANPAINT', name: 'Asian Paints Ltd' },
    { symbol: 'AXISBANK', name: 'Axis Bank Ltd' },
    { symbol: 'BAJFINANCE', name: 'Bajaj Finance Ltd' },
    { symbol: 'BHARTIARTL', name: 'Bharti Airtel Ltd' },
    { symbol: 'COALINDIA', name: 'Coal India Ltd' },
    { symbol: 'DRREDDY', name: 'Dr Reddys Laboratories' },
    { symbol: 'EICHERMOT', name: 'Eicher Motors Ltd' },
    { symbol: 'GRASIM', name: 'Grasim Industries Ltd' },
    { symbol: 'HCLTECH', name: 'HCL Technologies Ltd' },
    { symbol: 'HEROMOTOCO', name: 'Hero MotoCorp Ltd' },
    { symbol: 'HINDALCO', name: 'Hindalco Industries Ltd' },
    { symbol: 'HINDUNILVR', name: 'Hindustan Unilever Ltd' },
    { symbol: 'ITC', name: 'ITC Ltd' },
    { symbol: 'JSWSTEEL', name: 'JSW Steel Ltd' },
    { symbol: 'KOTAKBANK', name: 'Kotak Mahindra Bank' },
    { symbol: 'LT', name: 'Larsen & Toubro Ltd' },
    { symbol: 'M&M', name: 'Mahindra & Mahindra Ltd' },
  ];

  return nifty100Stocks.map((stock, index) => {
    const basePrice = 500 + Math.random() * 2000;
    const change = (Math.random() - 0.5) * 100;
    const changePercent = (change / basePrice) * 100;
    const support = basePrice * (0.85 + Math.random() * 0.1);
    const resistance = basePrice * (1.05 + Math.random() * 0.1);
    const rsi = 20 + Math.random() * 60;
    const macd = (Math.random() - 0.5) * 10;
    const volume = 100000 + Math.random() * 500000;
    const avgVolume = volume * (0.8 + Math.random() * 0.4);
    
    // Determine signal based on technical indicators
    let signal: 'BUY' | 'WAIT' | 'AVOID';
    const distanceFromSupport = (basePrice - support) / support;
    const distanceFromResistance = (resistance - basePrice) / basePrice;
    
    if (distanceFromSupport < 0.05 && rsi < 40 && macd > 0) {
      signal = 'BUY';
    } else if (distanceFromResistance < 0.05 || rsi > 70) {
      signal = 'AVOID';
    } else {
      signal = 'WAIT';
    }
    
    // Calculate risk/reward ratio
    const riskRewardRatio = distanceFromResistance / Math.max(distanceFromSupport, 0.01);
    
    // Calculate score (higher is better)
    let score = 50;
    if (signal === 'BUY') score += 30;
    if (rsi < 40) score += 15;
    if (macd > 0) score += 10;
    if (volume > avgVolume) score += 10;
    score += Math.min(riskRewardRatio * 10, 20);
    
    return {
      symbol: stock.symbol,
      name: stock.name,
      currentPrice: Math.round(basePrice * 100) / 100,
      change: Math.round(change * 100) / 100,
      changePercent: Math.round(changePercent * 100) / 100,
      support: Math.round(support * 100) / 100,
      resistance: Math.round(resistance * 100) / 100,
      rsi: Math.round(rsi * 100) / 100,
      macd: Math.round(macd * 100) / 100,
      volume: Math.round(volume),
      avgVolume: Math.round(avgVolume),
      signal,
      score: Math.round(score),
      riskRewardRatio: Math.round(riskRewardRatio * 100) / 100,
      lastUpdated: new Date().toISOString(),
    };
  }).sort((a, b) => b.score - a.score);
};

export const generateChartData = (symbol: string): ChartData => {
  const data = [];
  const now = new Date();
  let price = 1000 + Math.random() * 1000;
  
  // Generate 30 days of mock data
  for (let i = 29; i >= 0; i--) {
    const date = new Date(now);
    date.setDate(date.getDate() - i);
    
    const open = price;
    const change = (Math.random() - 0.5) * 50;
    const close = open + change;
    const high = Math.max(open, close) + Math.random() * 20;
    const low = Math.min(open, close) - Math.random() * 20;
    const volume = 100000 + Math.random() * 200000;
    
    data.push({
      time: date.toISOString().split('T')[0],
      open: Math.round(open * 100) / 100,
      high: Math.round(high * 100) / 100,
      low: Math.round(low * 100) / 100,
      close: Math.round(close * 100) / 100,
      volume: Math.round(volume),
    });
    
    price = close;
  }
  
  // Calculate support and resistance levels
  const prices = data.map(d => [d.high, d.low]).flat();
  const sortedPrices = [...prices].sort((a, b) => a - b);
  const supportLevels = [
    sortedPrices[Math.floor(sortedPrices.length * 0.1)],
    sortedPrices[Math.floor(sortedPrices.length * 0.25)],
  ];
  const resistanceLevels = [
    sortedPrices[Math.floor(sortedPrices.length * 0.75)],
    sortedPrices[Math.floor(sortedPrices.length * 0.9)],
  ];
  
  return {
    symbol,
    data,
    supportLevels,
    resistanceLevels,
  };
};