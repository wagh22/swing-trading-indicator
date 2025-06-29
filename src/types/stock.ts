export interface StockData {
  symbol: string;
  name: string;
  sector: string;
  timeframe: string;
  timeframeName: string;
  currentPrice: number;
  change: number;
  changePercent: number;
  support: number;
  resistance: number;
  potentialGainPercent: number;
  rsi: number;
  macd: number;
  volume: number;
  avgVolume: number;
  signal: 'BUY' | 'WAIT' | 'AVOID';
  score: number;
  riskRewardRatio: number;
  lastUpdated: string;
}

export interface ChartData {
  symbol: string;
  data: {
    time: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
  }[];
  supportLevels: number[];
  resistanceLevels: number[];
}

export interface FundamentalData {
  symbol: string;
  marketCap?: number;
  peRatio?: number;
  pbRatio?: number;
  dividendYield?: number;
  roe?: number;
  debtToEquity?: number;
  currentRatio?: number;
  revenueGrowth?: number;
  profitMargin?: number;
  bookValue?: number;
  eps?: number;
  beta?: number;
  fiftyTwoWeekHigh?: number;
  fiftyTwoWeekLow?: number;
  businessSummary?: string;
  keyMetrics?: string[];
  industry?: string;
  sector?: string;
  employees?: number;
  website?: string;
  lastUpdated: string;
}

export interface Timeframe {
  value: string;
  name: string;
  days: number;
}