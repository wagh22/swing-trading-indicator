import React from 'react';
import { Filter, Search } from 'lucide-react';

interface FilterBarProps {
  searchTerm: string;
  onSearchChange: (term: string) => void;
  signalFilter: string;
  onSignalFilterChange: (signal: string) => void;
}

export const FilterBar: React.FC<FilterBarProps> = ({
  searchTerm,
  onSearchChange,
  signalFilter,
  onSignalFilterChange,
}) => {
  return (
    <div className="bg-gray-800 rounded-lg p-4 mb-6 border border-gray-700">
      <div className="flex flex-col sm:flex-row gap-4 items-center">
        <div className="flex items-center space-x-2 text-gray-400">
          <Filter className="h-5 w-5" />
          <span className="font-medium">Filters</span>
        </div>
        
        <div className="flex-1 flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search stocks..."
              value={searchTerm}
              onChange={(e) => onSearchChange(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          
          <select
            value={signalFilter}
            onChange={(e) => onSignalFilterChange(e.target.value)}
            className="px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">All Signals</option>
            <option value="BUY">Buy Zone</option>
            <option value="WAIT">Wait</option>
            <option value="AVOID">Avoid</option>
          </select>
        </div>
      </div>
    </div>
  );
};