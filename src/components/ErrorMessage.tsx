import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

interface ErrorMessageProps {
  message: string;
  onRetry?: () => void;
  suggestion?: string;
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({ 
  message, 
  onRetry,
  suggestion 
}) => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] text-center px-6">
      <div className="bg-red-900/20 border border-red-700 rounded-lg p-8 max-w-md">
        <AlertCircle className="h-12 w-12 text-red-400 mx-auto mb-4" />
        <h3 className="text-xl font-semibold text-white mb-2">Connection Error</h3>
        <p className="text-red-400 mb-4">{message}</p>
        
        {suggestion && (
          <p className="text-gray-400 text-sm mb-6">{suggestion}</p>
        )}
        
        {onRetry && (
          <button
            onClick={onRetry}
            className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg text-white font-medium transition-colors mx-auto"
          >
            <RefreshCw className="h-4 w-4" />
            <span>Retry Connection</span>
          </button>
        )}
      </div>
    </div>
  );
};