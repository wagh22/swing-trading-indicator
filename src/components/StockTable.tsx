import React, { useState, useMemo } from 'react';
import { StockData } from '../types/stock';
import { TrendingUp, TrendingDown, Minus, Eye, Loader2, ChevronDown, ChevronUp, Building2, FileText } from 'lucide-react';
import { FundamentalModal } from './FundamentalModal';

interface StockTableProps {
  stocks: StockData[];
  onViewChart: (symbol: string) => void;
  isLoadingChart?: boolean;
  selectedTimeframe: string;
}

export const StockTable: React.FC<StockTableProps> = ({ 
  stocks, 
  onViewChart,
  isLoadingChart = false,
  selectedTimeframe
}) => {
  const [showAll, setShowAll] = useState(false);
  const [sortBy, setSortBy] = useState<'score' | 'potentialGain' | 'changePercent'>('score');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [groupBySector, setGroupBySector] = useState(true);
  const [expandedSectors, setExpandedSectors] = useState<Set<string>>(new Set());
  const [selectedFundamental, setSelectedFundamental] = useState<{symbol: string, name: string} | null>(null);

  const getSignalColor = (signal: string) => {
    switch (signal) {
      case 'BUY': return 'text-green-400 bg-green-900/20';
      case 'AVOID': return 'text-red-400 bg-red-900/20';
      default: return 'text-yellow-400 bg-yellow-900/20';
    }
  };

  const getChangeColor = (change: number) => {
    return change >= 0 ? 'text-green-400' : 'text-red-400';
  };

  const getChangeIcon = (change: number) => {
    if (change > 0) return <TrendingUp className="h-4 w-4" />;
    if (change < 0) return <TrendingDown className="h-4 w-4" />;
    return <Minus className="h-4 w-4" />;
  };

  const getPotentialGainColor = (gain: number) => {
    if (gain >= 20) return 'text-green-400 font-semibold';
    if (gain >= 15) return 'text-green-300';
    if (gain >= 10) return 'text-blue-400';
    if (gain >= 5) return 'text-yellow-400';
    return 'text-gray-400';
  };

  const handleSort = (column: 'score' | 'potentialGain' | 'changePercent') => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortOrder('desc');
    }
  };

  const sortedStocks = [...stocks].sort((a, b) => {
    let aValue: number, bValue: number;
    
    switch (sortBy) {
      case 'potentialGain':
        aValue = a.potentialGainPercent;
        bValue = b.potentialGainPercent;
        break;
      case 'changePercent':
        aValue = a.changePercent;
        bValue = b.changePercent;
        break;
      default:
        aValue = a.score;
        bValue = b.score;
    }
    
    return sortOrder === 'asc' ? aValue - bValue : bValue - aValue;
  });

  const groupedStocks = useMemo(() => {
    if (!groupBySector) {
      return { 'All Stocks': sortedStocks };
    }

    const groups: { [key: string]: StockData[] } = {};
    
    sortedStocks.forEach(stock => {
      const sector = stock.sector || 'Others';
      if (!groups[sector]) {
        groups[sector] = [];
      }
      groups[sector].push(stock);
    });

    // Sort sectors by average score
    const sortedSectors = Object.keys(groups).sort((a, b) => {
      const avgScoreA = groups[a].reduce((sum, stock) => sum + stock.score, 0) / groups[a].length;
      const avgScoreB = groups[b].reduce((sum, stock) => sum + stock.score, 0) / groups[b].length;
      return avgScoreB - avgScoreA;
    });

    const sortedGroups: { [key: string]: StockData[] } = {};
    sortedSectors.forEach(sector => {
      sortedGroups[sector] = groups[sector];
    });

    return sortedGroups;
  }, [sortedStocks, groupBySector]);

  const toggleSector = (sector: string) => {
    const newExpanded = new Set(expandedSectors);
    if (newExpanded.has(sector)) {
      newExpanded.delete(sector);
    } else {
      newExpanded.add(sector);
    }
    setExpandedSectors(newExpanded);
  };

  const getSectorStats = (sectorStocks: StockData[]) => {
    const buySignals = sectorStocks.filter(s => s.signal === 'BUY').length;
    const avgScore = sectorStocks.reduce((sum, stock) => sum + stock.score, 0) / sectorStocks.length;
    const avgPotentialGain = sectorStocks.reduce((sum, stock) => sum + stock.potentialGainPercent, 0) / sectorStocks.length;
    
    return { buySignals, avgScore, avgPotentialGain };
  };

  const handleViewFundamentals = (symbol: string, name: string) => {
    setSelectedFundamental({ symbol, name });
  };

  const renderStockRow = (stock: StockData, index: number, globalRank?: number) => (
    <tr key={stock.symbol} className="hover:bg-gray-700/50 transition-colors">
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="flex items-center">
          <span className="text-sm font-medium text-gray-400">
            #{globalRank || index + 1}
          </span>
          {stock.signal === 'BUY' && (
            <div className="ml-2 w-2 h-2 bg-green-400 rounded-full"></div>
          )}
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <div>
          <div className="text-sm font-medium text-white">{stock.symbol}</div>
          <div className="text-sm text-gray-400 truncate max-w-[200px]" title={stock.name}>
            {stock.name}
          </div>
          {!groupBySector && <div className="text-xs text-gray-500">{stock.sector}</div>}
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="text-sm font-medium text-white">₹{stock.currentPrice.toFixed(2)}</div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <div className={`flex items-center space-x-1 text-sm font-medium ${getChangeColor(stock.change)}`}>
          {getChangeIcon(stock.change)}
          <span>₹{Math.abs(stock.change).toFixed(2)}</span>
          <span>({stock.changePercent > 0 ? '+' : ''}{stock.changePercent.toFixed(2)}%)</span>
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getSignalColor(stock.signal)}`}>
          {stock.signal}
        </span>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <div className={`text-sm ${getPotentialGainColor(stock.potentialGainPercent)}`}>
          +{stock.potentialGainPercent.toFixed(1)}%
        </div>
        <div className="text-xs text-gray-500">
          ₹{(stock.currentPrice * stock.potentialGainPercent / 100).toFixed(0)} gain
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="text-sm text-white">{stock.rsi.toFixed(1)}</div>
        <div className="w-12 bg-gray-700 rounded-full h-1 mt-1">
          <div
            className={`h-1 rounded-full ${
              stock.rsi < 30 ? 'bg-green-500' : 
              stock.rsi > 70 ? 'bg-red-500' : 'bg-yellow-500'
            }`}
            style={{ width: `${Math.min(stock.rsi, 100)}%` }}
          ></div>
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="text-sm text-green-400">₹{stock.support.toFixed(2)}</div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="text-sm text-red-400">₹{stock.resistance.toFixed(2)}</div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="text-sm text-white">{stock.riskRewardRatio.toFixed(2)}</div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="flex items-center">
          <div className="text-sm font-medium text-white mr-2">{stock.score}</div>
          <div className="w-16 bg-gray-700 rounded-full h-2">
            <div
              className={`h-2 rounded-full ${
                stock.score >= 80 ? 'bg-green-500' :
                stock.score >= 60 ? 'bg-blue-500' :
                stock.score >= 40 ? 'bg-yellow-500' : 'bg-red-500'
              }`}
              style={{ width: `${Math.min(stock.score, 100)}%` }}
            ></div>
          </div>
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="flex items-center space-x-2">
          <button
            onClick={() => onViewChart(stock.symbol)}
            disabled={isLoadingChart}
            className="text-blue-400 hover:text-blue-300 transition-colors disabled:opacity-50 p-1 rounded hover:bg-gray-700"
            title="View Chart"
          >
            {isLoadingChart ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Eye className="h-4 w-4" />
            )}
          </button>
          <button
            onClick={() => handleViewFundamentals(stock.symbol, stock.name)}
            className="text-purple-400 hover:text-purple-300 transition-colors p-1 rounded hover:bg-gray-700"
            title="View Fundamentals"
          >
            <FileText className="h-4 w-4" />
          </button>
        </div>
      </td>
    </tr>
  );

  if (stocks.length === 0) {
    return (
      <div className="bg-gray-800 rounded-lg p-8 text-center">
        <p className="text-gray-400">No stocks found matching your criteria.</p>
      </div>
    );
  }

  const timeframeName = stocks[0]?.timeframeName || selectedTimeframe;
  const buySignals = stocks.filter(s => s.signal === 'BUY').length;
  const totalStocks = stocks.length;
  const totalSectors = Object.keys(groupedStocks).length;

  return (
    <>
      <div className="bg-gray-800 rounded-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-700">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h2 className="text-xl font-semibold text-white">NIFTY 100 Stock Analysis</h2>
              <p className="text-gray-400 text-sm mt-1">
                {totalStocks} stocks analyzed for {timeframeName} • {buySignals} buy signals
                {groupBySector && ` • ${totalSectors} sectors`}
              </p>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setGroupBySector(!groupBySector)}
                  className={`flex items-center gap-2 px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                    groupBySector 
                      ? 'bg-blue-600 text-white' 
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  <Building2 className="h-4 w-4" />
                  Group by Sector
                </button>
              </div>
              
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-400">Sort by:</span>
                <select
                  value={sortBy}
                  onChange={(e) => handleSort(e.target.value as any)}
                  className="bg-gray-700 border border-gray-600 rounded px-3 py-1 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="score">Score</option>
                  <option value="potentialGain">Potential Gain</option>
                  <option value="changePercent">Change %</option>
                </select>
                <button
                  onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                  className="text-gray-400 hover:text-white transition-colors"
                >
                  {sortOrder === 'desc' ? <ChevronDown className="h-4 w-4" /> : <ChevronUp className="h-4 w-4" />}
                </button>
              </div>
              
              {!showAll && totalStocks > 20 && !groupBySector && (
                <button
                  onClick={() => setShowAll(true)}
                  className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg text-white text-sm font-medium transition-colors"
                >
                  Show All {totalStocks}
                </button>
              )}
              
              {showAll && !groupBySector && (
                <button
                  onClick={() => setShowAll(false)}
                  className="bg-gray-600 hover:bg-gray-700 px-4 py-2 rounded-lg text-white text-sm font-medium transition-colors"
                >
                  Show Top 20
                </button>
              )}
            </div>
          </div>
        </div>
        
        <div className="overflow-x-auto">
          {groupBySector ? (
            // Grouped by sector view
            <div className="divide-y divide-gray-700">
              {Object.entries(groupedStocks).map(([sector, sectorStocks]) => {
                const isExpanded = expandedSectors.has(sector);
                const stats = getSectorStats(sectorStocks);
                const displayStocks = showAll ? sectorStocks : sectorStocks.slice(0, 10);
                
                return (
                  <div key={sector} className="bg-gray-800">
                    {/* Sector Header */}
                    <div 
                      className="px-6 py-4 bg-gray-750 cursor-pointer hover:bg-gray-700 transition-colors"
                      onClick={() => toggleSector(sector)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="flex items-center gap-2">
                            {isExpanded ? (
                              <ChevronDown className="h-5 w-5 text-gray-400" />
                            ) : (
                              <ChevronUp className="h-5 w-5 text-gray-400" />
                            )}
                            <Building2 className="h-5 w-5 text-blue-400" />
                            <h3 className="text-lg font-semibold text-white">{sector}</h3>
                          </div>
                          <span className="text-sm text-gray-400">({sectorStocks.length} stocks)</span>
                        </div>
                        
                        <div className="flex items-center gap-6 text-sm">
                          <div className="text-green-400">
                            <span className="font-medium">{stats.buySignals}</span> BUY signals
                          </div>
                          <div className="text-blue-400">
                            Avg Score: <span className="font-medium">{Math.round(stats.avgScore)}</span>
                          </div>
                          <div className="text-purple-400">
                            Avg Gain: <span className="font-medium">{stats.avgPotentialGain.toFixed(1)}%</span>
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    {/* Sector Stocks Table */}
                    {isExpanded && (
                      <div className="overflow-x-auto">
                        <table className="w-full">
                          <thead className="bg-gray-900">
                            <tr>
                              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Rank</th>
                              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Stock</th>
                              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Price</th>
                              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Change ({timeframeName})</th>
                              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Signal</th>
                              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Potential Gain</th>
                              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">RSI</th>
                              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Support</th>
                              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Resistance</th>
                              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">R/R Ratio</th>
                              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Score</th>
                              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Actions</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-gray-700">
                            {displayStocks.map((stock, index) => {
                              const globalRank = sortedStocks.findIndex(s => s.symbol === stock.symbol) + 1;
                              return renderStockRow(stock, index, globalRank);
                            })}
                          </tbody>
                        </table>
                        
                        {!showAll && sectorStocks.length > 10 && (
                          <div className="px-6 py-3 border-t border-gray-700 bg-gray-900/50">
                            <button
                              onClick={() => setShowAll(true)}
                              className="text-blue-400 hover:text-blue-300 text-sm font-medium transition-colors"
                            >
                              Show all {sectorStocks.length} stocks in {sector} →
                            </button>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            // Regular table view (ungrouped)
            <table className="w-full">
              <thead className="bg-gray-900">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Rank</th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Stock</th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Price</th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider cursor-pointer hover:text-white transition-colors"
                      onClick={() => handleSort('changePercent')}>
                    Change ({timeframeName})
                    {sortBy === 'changePercent' && (
                      sortOrder === 'desc' ? <ChevronDown className="inline h-3 w-3 ml-1" /> : <ChevronUp className="inline h-3 w-3 ml-1" />
                    )}
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Signal</th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider cursor-pointer hover:text-white transition-colors"
                      onClick={() => handleSort('potentialGain')}>
                    Potential Gain
                    {sortBy === 'potentialGain' && (
                      sortOrder === 'desc' ? <ChevronDown className="inline h-3 w-3 ml-1" /> : <ChevronUp className="inline h-3 w-3 ml-1" />
                    )}
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">RSI</th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Support</th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Resistance</th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">R/R Ratio</th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider cursor-pointer hover:text-white transition-colors"
                      onClick={() => handleSort('score')}>
                    Score
                    {sortBy === 'score' && (
                      sortOrder === 'desc' ? <ChevronDown className="inline h-3 w-3 ml-1" /> : <ChevronUp className="inline h-3 w-3 ml-1" />
                    )}
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {(showAll ? sortedStocks : sortedStocks.slice(0, 20)).map((stock, index) => 
                  renderStockRow(stock, index)
                )}
              </tbody>
            </table>
          )}
        </div>
        
        {!groupBySector && !showAll && totalStocks > 20 && (
          <div className="px-6 py-4 border-t border-gray-700 bg-gray-900/50">
            <div className="flex items-center justify-between">
              <p className="text-sm text-gray-400">
                Showing top 20 of {totalStocks} stocks
              </p>
              <button
                onClick={() => setShowAll(true)}
                className="text-blue-400 hover:text-blue-300 text-sm font-medium transition-colors"
              >
                View all {totalStocks} stocks →
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Fundamental Modal */}
      {selectedFundamental && (
        <FundamentalModal
          symbol={selectedFundamental.symbol}
          stockName={selectedFundamental.name}
          onClose={() => setSelectedFundamental(null)}
        />
      )}
    </>
  );
};