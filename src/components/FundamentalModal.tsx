import React, { useState, useEffect } from 'react';
import { X, Building2, TrendingUp, DollarSign, BarChart3, Users, Globe, Calendar, Loader2 } from 'lucide-react';
import { stockApi } from '../services/api';
import { FundamentalData } from '../types/stock';

interface FundamentalModalProps {
  symbol: string;
  stockName: string;
  onClose: () => void;
}

export const FundamentalModal: React.FC<FundamentalModalProps> = ({ 
  symbol, 
  stockName, 
  onClose 
}) => {
  const [fundamentalData, setFundamentalData] = useState<FundamentalData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchFundamentals = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        const response = await stockApi.getFundamentals(symbol);
        
        if (response.success && response.data) {
          setFundamentalData(response.data);
        } else {
          setError(response.error || 'Failed to fetch fundamental data');
        }
      } catch (err) {
        setError('Network error while fetching fundamental data');
      } finally {
        setIsLoading(false);
      }
    };

    fetchFundamentals();
  }, [symbol]);

  const formatNumber = (value: number | undefined, suffix: string = '', decimals: number = 2): string => {
    if (value === undefined || value === null) return 'N/A';
    
    if (suffix === 'Cr' && value > 1000000000) {
      return `₹${(value / 10000000).toFixed(decimals)} ${suffix}`;
    }
    
    if (suffix === '%' && typeof value === 'number') {
      return `${(value * 100).toFixed(decimals)}${suffix}`;
    }
    
    return `${value.toFixed(decimals)}${suffix}`;
  };

  const formatMarketCap = (value: number | undefined): string => {
    if (!value) return 'N/A';
    
    if (value >= 1000000000000) {
      return `₹${(value / 1000000000000).toFixed(2)} Lakh Cr`;
    } else if (value >= 10000000000) {
      return `₹${(value / 10000000000).toFixed(2)} Thousand Cr`;
    } else {
      return `₹${(value / 10000000).toFixed(2)} Cr`;
    }
  };

  const getValuationColor = (peRatio: number | undefined): string => {
    if (!peRatio) return 'text-gray-400';
    if (peRatio < 15) return 'text-green-400';
    if (peRatio > 30) return 'text-red-400';
    return 'text-yellow-400';
  };

  const getProfitabilityColor = (roe: number | undefined): string => {
    if (!roe) return 'text-gray-400';
    const roePercent = roe * 100;
    if (roePercent > 20) return 'text-green-400';
    if (roePercent > 15) return 'text-blue-400';
    if (roePercent < 10) return 'text-red-400';
    return 'text-yellow-400';
  };

  const getFinancialHealthColor = (ratio: number | undefined): string => {
    if (!ratio) return 'text-gray-400';
    if (ratio < 0.3) return 'text-green-400';
    if (ratio > 1.0) return 'text-red-400';
    return 'text-yellow-400';
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-gray-800 rounded-lg w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-gray-800 border-b border-gray-700 px-6 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-xl font-semibold text-white">{symbol} - Fundamental Analysis</h2>
              <p className="text-gray-400 text-sm">{stockName}</p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white transition-colors"
            >
              <X className="h-6 w-6" />
            </button>
          </div>
        </div>

        <div className="p-6">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-blue-500 mr-3" />
              <span className="text-gray-400">Loading fundamental data...</span>
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <div className="bg-red-900/20 border border-red-700 rounded-lg p-6">
                <p className="text-red-400 mb-2">Failed to load fundamental data</p>
                <p className="text-gray-400 text-sm">{error}</p>
              </div>
            </div>
          ) : fundamentalData ? (
            <div className="space-y-6">
              {/* Key Metrics Summary */}
              {fundamentalData.keyMetrics && fundamentalData.keyMetrics.length > 0 && (
                <div className="bg-gray-700 rounded-lg p-4">
                  <h3 className="text-lg font-semibold text-white mb-3 flex items-center">
                    <BarChart3 className="h-5 w-5 mr-2 text-blue-400" />
                    Key Insights
                  </h3>
                  <div className="space-y-2">
                    {fundamentalData.keyMetrics.map((insight, index) => (
                      <div key={index} className="text-gray-300 text-sm">
                        {insight}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Valuation Metrics */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-gray-700 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-gray-400 text-sm">Market Cap</p>
                      <p className="text-white text-lg font-semibold">
                        {formatMarketCap(fundamentalData.marketCap)}
                      </p>
                    </div>
                    <Building2 className="h-6 w-6 text-blue-400" />
                  </div>
                </div>

                <div className="bg-gray-700 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-gray-400 text-sm">P/E Ratio</p>
                      <p className={`text-lg font-semibold ${getValuationColor(fundamentalData.peRatio)}`}>
                        {formatNumber(fundamentalData.peRatio, '', 1)}
                      </p>
                    </div>
                    <TrendingUp className="h-6 w-6 text-purple-400" />
                  </div>
                </div>

                <div className="bg-gray-700 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-gray-400 text-sm">P/B Ratio</p>
                      <p className="text-white text-lg font-semibold">
                        {formatNumber(fundamentalData.pbRatio, '', 1)}
                      </p>
                    </div>
                    <BarChart3 className="h-6 w-6 text-green-400" />
                  </div>
                </div>

                <div className="bg-gray-700 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-gray-400 text-sm">Dividend Yield</p>
                      <p className="text-white text-lg font-semibold">
                        {formatNumber(fundamentalData.dividendYield, '%')}
                      </p>
                    </div>
                    <DollarSign className="h-6 w-6 text-yellow-400" />
                  </div>
                </div>
              </div>

              {/* Financial Performance */}
              <div>
                <h3 className="text-lg font-semibold text-white mb-4">Financial Performance</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  <div className="bg-gray-700 rounded-lg p-4">
                    <p className="text-gray-400 text-sm mb-1">Return on Equity</p>
                    <p className={`text-lg font-semibold ${getProfitabilityColor(fundamentalData.roe)}`}>
                      {formatNumber(fundamentalData.roe, '%')}
                    </p>
                  </div>

                  <div className="bg-gray-700 rounded-lg p-4">
                    <p className="text-gray-400 text-sm mb-1">Profit Margin</p>
                    <p className="text-white text-lg font-semibold">
                      {formatNumber(fundamentalData.profitMargin, '%')}
                    </p>
                  </div>

                  <div className="bg-gray-700 rounded-lg p-4">
                    <p className="text-gray-400 text-sm mb-1">Revenue Growth</p>
                    <p className="text-white text-lg font-semibold">
                      {formatNumber(fundamentalData.revenueGrowth, '%')}
                    </p>
                  </div>

                  <div className="bg-gray-700 rounded-lg p-4">
                    <p className="text-gray-400 text-sm mb-1">EPS</p>
                    <p className="text-white text-lg font-semibold">
                      ₹{formatNumber(fundamentalData.eps, '', 2)}
                    </p>
                  </div>

                  <div className="bg-gray-700 rounded-lg p-4">
                    <p className="text-gray-400 text-sm mb-1">Book Value</p>
                    <p className="text-white text-lg font-semibold">
                      ₹{formatNumber(fundamentalData.bookValue, '', 2)}
                    </p>
                  </div>

                  <div className="bg-gray-700 rounded-lg p-4">
                    <p className="text-gray-400 text-sm mb-1">Beta</p>
                    <p className="text-white text-lg font-semibold">
                      {formatNumber(fundamentalData.beta, '', 2)}
                    </p>
                  </div>
                </div>
              </div>

              {/* Financial Health */}
              <div>
                <h3 className="text-lg font-semibold text-white mb-4">Financial Health</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  <div className="bg-gray-700 rounded-lg p-4">
                    <p className="text-gray-400 text-sm mb-1">Debt to Equity</p>
                    <p className={`text-lg font-semibold ${getFinancialHealthColor(fundamentalData.debtToEquity)}`}>
                      {formatNumber(fundamentalData.debtToEquity, '', 2)}
                    </p>
                  </div>

                  <div className="bg-gray-700 rounded-lg p-4">
                    <p className="text-gray-400 text-sm mb-1">Current Ratio</p>
                    <p className="text-white text-lg font-semibold">
                      {formatNumber(fundamentalData.currentRatio, '', 2)}
                    </p>
                  </div>

                  <div className="bg-gray-700 rounded-lg p-4">
                    <p className="text-gray-400 text-sm mb-1">52W High</p>
                    <p className="text-green-400 text-lg font-semibold">
                      ₹{formatNumber(fundamentalData.fiftyTwoWeekHigh, '', 2)}
                    </p>
                  </div>

                  <div className="bg-gray-700 rounded-lg p-4">
                    <p className="text-gray-400 text-sm mb-1">52W Low</p>
                    <p className="text-red-400 text-lg font-semibold">
                      ₹{formatNumber(fundamentalData.fiftyTwoWeekLow, '', 2)}
                    </p>
                  </div>

                  {fundamentalData.employees && (
                    <div className="bg-gray-700 rounded-lg p-4">
                      <p className="text-gray-400 text-sm mb-1 flex items-center">
                        <Users className="h-4 w-4 mr-1" />
                        Employees
                      </p>
                      <p className="text-white text-lg font-semibold">
                        {fundamentalData.employees.toLocaleString()}
                      </p>
                    </div>
                  )}

                  {fundamentalData.website && (
                    <div className="bg-gray-700 rounded-lg p-4">
                      <p className="text-gray-400 text-sm mb-1 flex items-center">
                        <Globe className="h-4 w-4 mr-1" />
                        Website
                      </p>
                      <a 
                        href={fundamentalData.website} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-blue-400 hover:text-blue-300 text-sm truncate block"
                      >
                        {fundamentalData.website.replace('https://', '').replace('http://', '')}
                      </a>
                    </div>
                  )}
                </div>
              </div>

              {/* Business Summary */}
              {fundamentalData.businessSummary && (
                <div>
                  <h3 className="text-lg font-semibold text-white mb-4">Business Overview</h3>
                  <div className="bg-gray-700 rounded-lg p-4">
                    <p className="text-gray-300 text-sm leading-relaxed">
                      {fundamentalData.businessSummary}
                    </p>
                  </div>
                </div>
              )}

              {/* Last Updated */}
              <div className="flex items-center justify-center text-gray-500 text-xs">
                <Calendar className="h-4 w-4 mr-1" />
                Last updated: {new Date(fundamentalData.lastUpdated).toLocaleString()}
              </div>
            </div>
          ) : (
            <div className="text-center py-12">
              <p className="text-gray-400">No fundamental data available</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};