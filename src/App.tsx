import React, { useState, useEffect, useMemo } from 'react';
import { Header } from './components/Header';
import { StatsCards } from './components/StatsCards';
import { TimeframeSelector } from './components/TimeframeSelector';
import { FilterBar } from './components/FilterBar';
import { StockTable } from './components/StockTable';
import { StockChart } from './components/StockChart';
import { LoadingSpinner } from './components/LoadingSpinner';
import { ErrorMessage } from './components/ErrorMessage';
import { stockApi } from './services/api';
import { StockData, ChartData, Timeframe } from './types/stock';

function App() {
  const [stocks, setStocks] = useState<StockData[]>([]);
  const [timeframes, setTimeframes] = useState<Timeframe[]>([]);
  const [selectedTimeframe, setSelectedTimeframe] = useState('1M');
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [signalFilter, setSignalFilter] = useState('');
  const [selectedChart, setSelectedChart] = useState<ChartData | null>(null);
  const [isLoadingChart, setIsLoadingChart] = useState(false);

  const loadTimeframes = async () => {
    try {
      const response = await stockApi.getTimeframes();
      if (response.success && response.data) {
        setTimeframes(response.data);
      }
    } catch (err) {
      console.error('Failed to load timeframes:', err);
    }
  };

  const loadData = async (timeframe: string = selectedTimeframe) => {
    try {
      setError(null);
      const response = await stockApi.getStocks(timeframe);
      
      if (response.success && response.data) {
        setStocks(response.data);
      } else {
        setError(response.error || 'Failed to load stock data');
      }
    } catch (err) {
      setError('Network error: Unable to connect to backend API');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await loadData();
  };

  const handleTimeframeChange = async (timeframe: string) => {
    setSelectedTimeframe(timeframe);
    setIsRefreshing(true);
    await loadData(timeframe);
  };

  useEffect(() => {
    const initializeApp = async () => {
      await loadTimeframes();
      await loadData();
    };
    initializeApp();
  }, []);

  const filteredStocks = useMemo(() => {
    return stocks.filter(stock => {
      const matchesSearch = stock.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           stock.name.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesSignal = !signalFilter || stock.signal === signalFilter;
      
      return matchesSearch && matchesSignal;
    });
  }, [stocks, searchTerm, signalFilter]);

  const handleViewChart = async (symbol: string) => {
    setIsLoadingChart(true);
    try {
      // Get chart data based on selected timeframe
      const timeframeDays = timeframes.find(t => t.value === selectedTimeframe)?.days || 30;
      const response = await stockApi.getChartData(symbol, timeframeDays);
      
      if (response.success && response.data) {
        // Transform API response to match ChartData interface
        const chartData: ChartData = {
          symbol: response.data.symbol,
          data: response.data.data,
          supportLevels: response.data.supportLevels,
          resistanceLevels: response.data.resistanceLevels,
        };
        setSelectedChart(chartData);
      } else {
        setError(response.error || 'Failed to load chart data');
      }
    } catch (err) {
      setError('Failed to load chart data');
    } finally {
      setIsLoadingChart(false);
    }
  };

  const handleCloseChart = () => {
    setSelectedChart(null);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-900">
        <Header onRefresh={handleRefresh} isRefreshing={false} />
        <LoadingSpinner message="Loading stock analysis..." />
      </div>
    );
  }

  if (error && stocks.length === 0) {
    return (
      <div className="min-h-screen bg-gray-900">
        <Header onRefresh={handleRefresh} isRefreshing={isRefreshing} />
        <ErrorMessage 
          message={error} 
          onRetry={handleRefresh}
          suggestion="Make sure the Python backend is running on localhost:8000"
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900">
      <Header onRefresh={handleRefresh} isRefreshing={isRefreshing} />
      
      <main className="max-w-7xl mx-auto px-6 py-8">
        {error && (
          <div className="mb-6">
            <div className="bg-yellow-900/20 border border-yellow-700 rounded-lg p-4">
              <p className="text-yellow-400 text-sm">{error}</p>
            </div>
          </div>
        )}
        
        <StatsCards stocks={stocks} selectedTimeframe={selectedTimeframe} />
        
        <TimeframeSelector
          timeframes={timeframes}
          selectedTimeframe={selectedTimeframe}
          onTimeframeChange={handleTimeframeChange}
          isLoading={isRefreshing}
        />
        
        <FilterBar
          searchTerm={searchTerm}
          onSearchChange={setSearchTerm}
          signalFilter={signalFilter}
          onSignalFilterChange={setSignalFilter}
        />
        
        <StockTable
          stocks={filteredStocks}
          onViewChart={handleViewChart}
          isLoadingChart={isLoadingChart}
          selectedTimeframe={selectedTimeframe}
        />
      </main>
      
      {selectedChart && (
        <StockChart
          chartData={selectedChart}
          onClose={handleCloseChart}
        />
      )}
    </div>
  );
}

export default App;