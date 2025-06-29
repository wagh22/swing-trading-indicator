# NIFTY 100 Stock Analysis Flask API

A comprehensive Flask-based REST API for analyzing NIFTY 100 stocks with swing trading strategies.

## 🚀 Features

- **Modern Flask Framework**: Professional REST API with proper error handling
- **CORS Support**: Cross-origin requests enabled for frontend integration
- **Stock Universe**: NIFTY 100 index stocks
- **Historical Data**: Simulated OHLCV data stored in SQLite
- **Multi-timeframe Analysis**: 1W, 1M, 3M, 6M, 1Y timeframes
- **Technical Analysis**: 
  - Support & Resistance level detection using pivot points
  - RSI (Relative Strength Index) calculation
  - MACD (Moving Average Convergence Divergence)
  - Volume analysis
  - Potential gain calculations
- **Trading Signals**: 
  - BUY: Near support + oversold + positive momentum
  - WAIT: Neutral conditions
  - AVOID: Near resistance or overbought
- **Scoring System**: Composite score based on multiple factors
- **Risk/Reward Analysis**: Calculated ratios for each stock

## 📦 Installation

```bash
cd backend
pip install -r requirements.txt
```

## 🏃‍♂️ Running the Server

```bash
cd backend
python app.py
```

The server will start on `http://localhost:8000`

## 🌐 API Endpoints

### GET /api/health
Health check endpoint to verify API status.

**Response:**
```json
{
  "success": true,
  "message": "Stock Analysis Flask API is running",
  "timestamp": "2025-01-27T...",
  "version": "2.0.0"
}
```

### GET /api/stocks?timeframe=1M
Returns analysis for all NIFTY 100 stocks with technical indicators and trading signals.

**Parameters:**
- `timeframe` (optional): Analysis timeframe (1W, 1M, 3M, 6M, 1Y). Default: 1M

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "symbol": "HDFCBANK",
      "name": "HDFC Bank Ltd",
      "sector": "Banking",
      "timeframe": "1M",
      "timeframeName": "1 Month",
      "currentPrice": 1650.25,
      "change": 12.50,
      "changePercent": 0.76,
      "support": 1580.00,
      "resistance": 1720.00,
      "potentialGainPercent": 4.23,
      "rsi": 45.2,
      "macd": 2.1,
      "volume": 250000,
      "avgVolume": 200000,
      "signal": "BUY",
      "score": 85,
      "riskRewardRatio": 2.5,
      "lastUpdated": "2025-01-27T..."
    }
  ],
  "timeframe": "1M",
  "timestamp": "2025-01-27T...",
  "count": 30
}
```

### GET /api/stock/<symbol>?timeframe=1M
Returns analysis for a single stock.

**Parameters:**
- `symbol`: Stock symbol (required, case-insensitive)
- `timeframe` (optional): Analysis timeframe. Default: 1M

**Response:**
```json
{
  "success": true,
  "data": {
    "symbol": "HDFCBANK",
    "name": "HDFC Bank Ltd",
    // ... same structure as stocks endpoint
  }
}
```

### GET /api/chart?symbol=SYMBOL&days=30
Returns chart data for a specific stock with support/resistance levels.

**Parameters:**
- `symbol`: Stock symbol (required, case-insensitive)
- `days`: Number of days of data (1-365, default: 30)

**Response:**
```json
{
  "success": true,
  "data": {
    "symbol": "HDFCBANK",
    "data": [
      {
        "time": "2025-01-01",
        "open": 1640.00,
        "high": 1655.00,
        "low": 1635.00,
        "close": 1650.25,
        "volume": 250000
      }
    ],
    "supportLevels": [1580.00],
    "resistanceLevels": [1720.00]
  }
}
```

### GET /api/timeframes
Returns available analysis timeframes.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "value": "1W",
      "name": "1 Week",
      "days": 7
    },
    {
      "value": "1M",
      "name": "1 Month",
      "days": 30
    }
  ]
}
```

## 🔧 Technical Analysis Details

### Support & Resistance Detection
- Uses pivot point analysis with configurable window
- Identifies local minima (support) and maxima (resistance)
- Finds most significant levels relative to current price

### RSI Calculation
- 14-period Relative Strength Index
- Identifies overbought (>70) and oversold (<30) conditions

### MACD Calculation
- Moving Average Convergence Divergence
- Uses 12-period and 26-period moving averages
- Positive values indicate upward momentum

### Potential Gain Calculation
- Calculates percentage gain from current price to resistance level
- Helps identify stocks with highest upside potential
- Color-coded in frontend based on gain percentage

### Trading Signal Logic
- **BUY**: Price within 5% of support + RSI < 40 + MACD > 0
- **AVOID**: Price within 5% of resistance OR RSI > 70
- **WAIT**: All other conditions

### Scoring Algorithm
Base score of 50 with adjustments for:
- Signal type (+30 for BUY, -20 for AVOID)
- RSI levels (+20 for very oversold, -15 for overbought)
- MACD momentum (+10 for positive)
- Volume activity (+10 for high volume, -5 for low)
- Risk/reward ratio (+20 for >3:1 ratio)
- Potential gain (+25 for >20% gain)
- Timeframe-specific adjustments

## 🗄️ Database Schema

### stock_prices
- Historical OHLCV data for all stocks
- Unique constraint on (symbol, date)

### stock_analysis
- Current analysis results for each stock and timeframe
- Unique constraint on (symbol, timeframe)
- Updated on each API call

## 🏗️ Architecture Improvements

### Flask Benefits Over Basic HTTP Server:
- **Professional Framework**: Industry-standard web framework
- **Better Error Handling**: Proper HTTP status codes and error responses
- **Request Validation**: Built-in parameter validation and parsing
- **CORS Support**: Easy cross-origin request handling
- **Extensibility**: Easy to add authentication, rate limiting, etc.
- **Development Tools**: Debug mode, auto-reload, better logging

### New Features:
- **Individual Stock Endpoint**: Get analysis for single stock
- **Parameter Validation**: Proper validation with error messages
- **Enhanced Error Responses**: Detailed error information
- **Version Information**: API versioning support
- **Request Counting**: Track API usage

## 🚀 Production Enhancements

For production deployment, consider:
- **Authentication**: JWT tokens or API keys
- **Rate Limiting**: Prevent API abuse
- **Caching**: Redis for performance optimization
- **Real Data**: Integration with market data providers
- **Database**: PostgreSQL for scalability
- **Monitoring**: Logging and metrics collection
- **Docker**: Containerization for deployment
- **Load Balancing**: Handle multiple requests
- **SSL/HTTPS**: Secure connections

## 🔍 Error Handling

The API provides detailed error responses:

```json
{
  "success": false,
  "error": "Invalid timeframe. Supported: ['1W', '1M', '3M', '6M', '1Y']"
}
```

Common HTTP status codes:
- `200`: Success
- `400`: Bad Request (invalid parameters)
- `404`: Not Found (stock/endpoint not found)
- `500`: Internal Server Error

## 📊 Usage Examples

```bash
# Get all stocks for 1 month timeframe
curl "http://localhost:8000/api/stocks?timeframe=1M"

# Get specific stock analysis
curl "http://localhost:8000/api/stock/HDFCBANK?timeframe=3M"

# Get chart data for 90 days
curl "http://localhost:8000/api/chart?symbol=RELIANCE&days=90"

# Check API health
curl "http://localhost:8000/api/health"
```