import React from 'react';
import { Clock } from 'lucide-react';
import { Timeframe } from '../types/stock';

interface TimeframeSelectorProps {
  timeframes: Timeframe[];
  selectedTimeframe: string;
  onTimeframeChange: (timeframe: string) => void;
  isLoading?: boolean;
}

export const TimeframeSelector: React.FC<TimeframeSelectorProps> = ({
  timeframes,
  selectedTimeframe,
  onTimeframeChange,
  isLoading = false
}) => {
  return (
    <div className="bg-gray-800 rounded-lg p-4 mb-6 border border-gray-700">
      <div className="flex flex-col sm:flex-row gap-4 items-center">
        <div className="flex items-center space-x-2 text-gray-400">
          <Clock className="h-5 w-5" />
          <span className="font-medium">Analysis Timeframe</span>
        </div>
        
        <div className="flex flex-wrap gap-2">
          {timeframes.map((timeframe) => (
            <button
              key={timeframe.value}
              onClick={() => onTimeframeChange(timeframe.value)}
              disabled={isLoading}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50 ${
                selectedTimeframe === timeframe.value
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              {timeframe.name}
            </button>
          ))}
        </div>
        
        {isLoading && (
          <div className="text-sm text-gray-400">
            Analyzing {timeframes.find(t => t.value === selectedTimeframe)?.name.toLowerCase()}...
          </div>
        )}
      </div>
    </div>
  );
};