const API_BASE_URL = 'http://localhost:8000';

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  timestamp?: string;
  timeframe?: string;
}

export const stockApi = {
  async getStocks(timeframe: string = '1M'): Promise<ApiResponse<any[]>> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/stocks?timeframe=${timeframe}`);
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error fetching stocks:', error);
      return {
        success: false,
        error: 'Failed to fetch stock data. Make sure the Python backend is running on localhost:8000'
      };
    }
  },

  async getChartData(symbol: string, days: number = 30): Promise<ApiResponse<any>> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chart?symbol=${symbol}&days=${days}`);
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error fetching chart data:', error);
      return {
        success: false,
        error: 'Failed to fetch chart data'
      };
    }
  },

  async getFundamentals(symbol: string): Promise<ApiResponse<any>> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/fundamentals/${symbol}`);
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error fetching fundamental data:', error);
      return {
        success: false,
        error: 'Failed to fetch fundamental data'
      };
    }
  },

  async getTimeframes(): Promise<ApiResponse<any[]>> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/timeframes`);
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error fetching timeframes:', error);
      return {
        success: false,
        error: 'Failed to fetch timeframes'
      };
    }
  },

  async healthCheck(): Promise<ApiResponse<any>> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/health`);
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error checking API health:', error);
      return {
        success: false,
        error: 'Backend API is not available'
      };
    }
  }
};