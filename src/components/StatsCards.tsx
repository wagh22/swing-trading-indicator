import React from 'react';
import { StockData } from '../types/stock';
import { TrendingUp, TrendingDown, Target, AlertTriangle, Percent } from 'lucide-react';

interface StatsCardsProps {
  stocks: StockData[];
  selectedTimeframe: string;
}

export const StatsCards: React.FC<StatsCardsProps> = ({ stocks, selectedTimeframe }) => {
  const buySignals = stocks.filter(s => s.signal === 'BUY').length;
  const avoidSignals = stocks.filter(s => s.signal === 'AVOID').length;
  const waitSignals = stocks.filter(s => s.signal === 'WAIT').length;
  const avgScore = stocks.reduce((sum, stock) => sum + stock.score, 0) / stocks.length;
  
  // Calculate average potential gain for BUY signals
  const buyStocks = stocks.filter(s => s.signal === 'BUY');
  const avgPotentialGain = buyStocks.length > 0 
    ? buyStocks.reduce((sum, stock) => sum + stock.potentialGainPercent, 0) / buyStocks.length 
    : 0;

  // Get timeframe name for display
  const timeframeName = stocks.length > 0 ? stocks[0].timeframeName : selectedTimeframe;

  const cards = [
    {
      title: 'Buy Signals',
      value: buySignals,
      subtitle: `Stocks in buy zone (${timeframeName})`,
      icon: TrendingUp,
      color: 'text-green-400',
      bgColor: 'bg-green-900/20',
    },
    {
      title: 'Avg Potential Gain',
      value: `${avgPotentialGain.toFixed(1)}%`,
      subtitle: `Expected upside for buy signals`,
      icon: Percent,
      color: 'text-blue-400',
      bgColor: 'bg-blue-900/20',
    },
    {
      title: 'Avoid Signals',
      value: avoidSignals,
      subtitle: `Overbought stocks`,
      icon: TrendingDown,
      color: 'text-red-400',
      bgColor: 'bg-red-900/20',
    },
    {
      title: 'Avg Score',
      value: Math.round(avgScore),
      subtitle: `Overall market strength`,
      icon: Target,
      color: 'text-purple-400',
      bgColor: 'bg-purple-900/20',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      {cards.map((card) => (
        <div key={card.title} className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm font-medium">{card.title}</p>
              <p className="text-2xl font-bold text-white mt-1">{card.value}</p>
              <p className="text-gray-500 text-xs mt-1">{card.subtitle}</p>
            </div>
            <div className={`p-3 rounded-lg ${card.bgColor}`}>
              <card.icon className={`h-6 w-6 ${card.color}`} />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};