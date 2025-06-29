from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import sqlite3
import random
import math
from datetime import datetime, timedelta
import threading
import time
import requests
import yfinance as yf
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import logging
import  NSA_Index_Extractor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NSEStockAnalyzer:
    def __init__(self):
        self.db_path = 'stocks.db'
        self.init_database()
        
        # NSE NIFTY 100 stocks with Yahoo Finance symbols
        # self.nifty_100_stocks = [
        #     {'symbol': 'HDFCBANK.NS', 'display_symbol': 'HDFCBANK', 'name': 'HDFC Bank Ltd', 'sector': 'Banking'},
        #     {'symbol': 'INFY.NS', 'display_symbol': 'INFY', 'name': 'Infosys Ltd', 'sector': 'IT'},
        #     {'symbol': 'TCS.NS', 'display_symbol': 'TCS', 'name': 'Tata Consultancy Services', 'sector': 'IT'},
        #     {'symbol': 'RELIANCE.NS', 'display_symbol': 'RELIANCE', 'name': 'Reliance Industries Ltd', 'sector': 'Oil & Gas'},
        #     {'symbol': 'ICICIBANK.NS', 'display_symbol': 'ICICIBANK', 'name': 'ICICI Bank Ltd', 'sector': 'Banking'},
        #     {'symbol': 'WIPRO.NS', 'display_symbol': 'WIPRO', 'name': 'Wipro Ltd', 'sector': 'IT'},
        #     {'symbol': 'SBIN.NS', 'display_symbol': 'SBIN', 'name': 'State Bank of India', 'sector': 'Banking'},
        #     {'symbol': 'ADANIPORTS.NS', 'display_symbol': 'ADANIPORTS', 'name': 'Adani Ports & SEZ Ltd', 'sector': 'Infrastructure'},
        #     {'symbol': 'ASIANPAINT.NS', 'display_symbol': 'ASIANPAINT', 'name': 'Asian Paints Ltd', 'sector': 'Paints'},
        #     {'symbol': 'AXISBANK.NS', 'display_symbol': 'AXISBANK', 'name': 'Axis Bank Ltd', 'sector': 'Banking'},
        #     {'symbol': 'BAJFINANCE.NS', 'display_symbol': 'BAJFINANCE', 'name': 'Bajaj Finance Ltd', 'sector': 'NBFC'},
        #     {'symbol': 'BHARTIARTL.NS', 'display_symbol': 'BHARTIARTL', 'name': 'Bharti Airtel Ltd', 'sector': 'Telecom'},
        #     {'symbol': 'COALINDIA.NS', 'display_symbol': 'COALINDIA', 'name': 'Coal India Ltd', 'sector': 'Mining'},
        #     {'symbol': 'DRREDDY.NS', 'display_symbol': 'DRREDDY', 'name': 'Dr Reddys Laboratories', 'sector': 'Pharma'},
        #     {'symbol': 'EICHERMOT.NS', 'display_symbol': 'EICHERMOT', 'name': 'Eicher Motors Ltd', 'sector': 'Auto'},
        #     {'symbol': 'GRASIM.NS', 'display_symbol': 'GRASIM', 'name': 'Grasim Industries Ltd', 'sector': 'Cement'},
        #     {'symbol': 'HCLTECH.NS', 'display_symbol': 'HCLTECH', 'name': 'HCL Technologies Ltd', 'sector': 'IT'},
        #     {'symbol': 'HEROMOTOCO.NS', 'display_symbol': 'HEROMOTOCO', 'name': 'Hero MotoCorp Ltd', 'sector': 'Auto'},
        #     {'symbol': 'HINDALCO.NS', 'display_symbol': 'HINDALCO', 'name': 'Hindalco Industries Ltd', 'sector': 'Metals'},
        #     {'symbol': 'HINDUNILVR.NS', 'display_symbol': 'HINDUNILVR', 'name': 'Hindustan Unilever Ltd', 'sector': 'FMCG'},
        #     {'symbol': 'ITC.NS', 'display_symbol': 'ITC', 'name': 'ITC Ltd', 'sector': 'FMCG'},
        #     {'symbol': 'JSWSTEEL.NS', 'display_symbol': 'JSWSTEEL', 'name': 'JSW Steel Ltd', 'sector': 'Steel'},
        #     {'symbol': 'KOTAKBANK.NS', 'display_symbol': 'KOTAKBANK', 'name': 'Kotak Mahindra Bank', 'sector': 'Banking'},
        #     {'symbol': 'LT.NS', 'display_symbol': 'LT', 'name': 'Larsen & Toubro Ltd', 'sector': 'Engineering'},
        #     {'symbol': 'M&M.NS', 'display_symbol': 'M&M', 'name': 'Mahindra & Mahindra Ltd', 'sector': 'Auto'},
        #     {'symbol': 'MARUTI.NS', 'display_symbol': 'MARUTI', 'name': 'Maruti Suzuki India Ltd', 'sector': 'Auto'},
        #     {'symbol': 'NESTLEIND.NS', 'display_symbol': 'NESTLEIND', 'name': 'Nestle India Ltd', 'sector': 'FMCG'},
        #     {'symbol': 'NTPC.NS', 'display_symbol': 'NTPC', 'name': 'NTPC Ltd', 'sector': 'Power'},
        #     {'symbol': 'ONGC.NS', 'display_symbol': 'ONGC', 'name': 'Oil & Natural Gas Corp', 'sector': 'Oil & Gas'},
        #     {'symbol': 'POWERGRID.NS', 'display_symbol': 'POWERGRID', 'name': 'Power Grid Corp of India', 'sector': 'Power'},
        # ]
        self.nifty_100_stocks = NSA_Index_Extractor.fetch_nifty_100_dynamic()
        
        # Extended timeframe configurations with long-term options
        self.timeframes = {
            '1W': {'days': 7, 'name': '1 Week'},
            '1M': {'days': 30, 'name': '1 Month'},
            '3M': {'days': 90, 'name': '3 Months'},
            '6M': {'days': 180, 'name': '6 Months'},
            '1Y': {'days': 365, 'name': '1 Year'},
            '2Y': {'days': 730, 'name': '2 Years'},
            '3Y': {'days': 1095, 'name': '3 Years'},
            '4Y': {'days': 1460, 'name': '4 Years'},
            '5Y': {'days': 1825, 'name': '5 Years'},
            '10Y': {'days': 3650, 'name': '10 Years'}
        }
        
        # Cache for stock data to avoid frequent API calls
        self.data_cache = {}
        self.cache_expiry = {}
        self.cache_duration = 300  # 5 minutes cache
    
    def init_database(self):
        """Initialize SQLite database with stock data tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                date TEXT NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume INTEGER NOT NULL,
                UNIQUE(symbol, date)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                name TEXT NOT NULL,
                sector TEXT,
                timeframe TEXT NOT NULL,
                current_price REAL NOT NULL,
                change_amount REAL NOT NULL,
                change_percent REAL NOT NULL,
                support_level REAL NOT NULL,
                resistance_level REAL NOT NULL,
                potential_gain_percent REAL NOT NULL,
                rsi REAL NOT NULL,
                macd REAL NOT NULL,
                volume INTEGER NOT NULL,
                avg_volume INTEGER NOT NULL,
                signal TEXT NOT NULL,
                score INTEGER NOT NULL,
                risk_reward_ratio REAL NOT NULL,
                last_updated TEXT NOT NULL,
                UNIQUE(symbol, timeframe)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def is_cache_valid(self, symbol):
        """Check if cached data is still valid"""
        if symbol not in self.cache_expiry:
            return False
        return datetime.now() < self.cache_expiry[symbol]
    
    def fetch_stock_data_yfinance(self, symbol, period='1y'):
        """Fetch real stock data from Yahoo Finance"""
        try:
            # Check cache first
            cache_key = f"{symbol}_{period}"
            if self.is_cache_valid(cache_key) and cache_key in self.data_cache:
                logger.info(f"Using cached data for {symbol}")
                return self.data_cache[cache_key]
            
            logger.info(f"Fetching real data for {symbol} from Yahoo Finance...")
            
            # Create ticker object
            ticker = yf.Ticker(symbol)
            
            # Get historical data
            hist = ticker.history(period=period)
            
            if hist.empty:
                logger.warning(f"No data found for {symbol}")
                return None
            
            # Convert to our format
            stock_data = []
            for date, row in hist.iterrows():
                stock_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': int(row['Volume'])
                })
            
            # Cache the data
            self.data_cache[cache_key] = stock_data
            self.cache_expiry[cache_key] = datetime.now() + timedelta(seconds=self.cache_duration)
            
            logger.info(f"Successfully fetched {len(stock_data)} days of data for {symbol}")
            return stock_data
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            return None
    
    def store_stock_data(self, display_symbol, stock_data):
        """Store fetched stock data in database"""
        if not stock_data:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            for data_point in stock_data:
                cursor.execute('''
                    INSERT OR REPLACE INTO stock_prices 
                    (symbol, date, open, high, low, close, volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    display_symbol,
                    data_point['date'],
                    data_point['open'],
                    data_point['high'],
                    data_point['low'],
                    data_point['close'],
                    data_point['volume']
                ))
            
            conn.commit()
            logger.info(f"Stored {len(stock_data)} records for {display_symbol}")
            
        except Exception as e:
            logger.error(f"Error storing data for {display_symbol}: {str(e)}")
        finally:
            conn.close()
    
    def get_timeframe_days(self, timeframe):
        """Get number of days for a given timeframe"""
        return self.timeframes.get(timeframe, {'days': 30})['days']
    
    def calculate_rsi(self, prices, period=14):
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            return 50.0
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        if len(gains) < period:
            return 50.0
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return round(rsi, 2)
    
    def calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """Calculate MACD (Moving Average Convergence Divergence)"""
        if len(prices) < slow:
            return 0.0
        
        # Calculate exponential moving averages
        def ema(data, period):
            if len(data) < period:
                return data[-1] if data else 0
            
            multiplier = 2 / (period + 1)
            ema_values = [sum(data[:period]) / period]  # First EMA is SMA
            
            for i in range(period, len(data)):
                ema_val = (data[i] * multiplier) + (ema_values[-1] * (1 - multiplier))
                ema_values.append(ema_val)
            
            return ema_values[-1]
        
        fast_ema = ema(prices, fast)
        slow_ema = ema(prices, slow)
        
        macd_line = fast_ema - slow_ema
        return round(macd_line, 2)
    
    def find_support_resistance(self, prices, window=20):
        """Find support and resistance levels using pivot points"""
        if len(prices) < window * 2:
            return min(prices) * 0.95, max(prices) * 1.05
        
        # Find local minima and maxima
        supports = []
        resistances = []
        
        for i in range(window, len(prices) - window):
            # Check if current price is a local minimum (support)
            is_support = all(prices[i] <= prices[j] for j in range(i-window, i+window+1) if j != i)
            if is_support:
                supports.append(prices[i])
            
            # Check if current price is a local maximum (resistance)
            is_resistance = all(prices[i] >= prices[j] for j in range(i-window, i+window+1) if j != i)
            if is_resistance:
                resistances.append(prices[i])
        
        # Get most significant levels
        current_price = prices[-1]
        
        # Find nearest support below current price
        valid_supports = [s for s in supports if s < current_price]
        support = max(valid_supports) if valid_supports else min(prices) * 0.95
        
        # Find nearest resistance above current price
        valid_resistances = [r for r in resistances if r > current_price]
        resistance = min(valid_resistances) if valid_resistances else max(prices) * 1.05
        
        return round(support, 2), round(resistance, 2)
    
    def calculate_potential_gain(self, current_price, resistance):
        """Calculate potential gain percentage from current price to resistance"""
        if current_price <= 0 or resistance <= current_price:
            return 0.0
        
        potential_gain = ((resistance - current_price) / current_price) * 100
        return round(potential_gain, 2)
    
    def analyze_stock(self, stock_info, timeframe='1M'):
        """Perform comprehensive technical analysis on a stock for given timeframe"""
        symbol = stock_info['symbol']
        display_symbol = stock_info['display_symbol']
        analysis_days = self.get_timeframe_days(timeframe)
        
        # Fetch real stock data with updated period mapping for long-term timeframes
        period_map = {
            '1W': '1mo',
            '1M': '3mo', 
            '3M': '6mo',
            '6M': '1y',
            '1Y': '2y',
            '2Y': '5y',
            '3Y': '5y',
            '4Y': '10y',
            '5Y': '10y',
            '10Y': 'max'  # Maximum available data
        }
        period = period_map.get(timeframe, '1y')
        
        stock_data = self.fetch_stock_data_yfinance(symbol, period)
        
        if not stock_data:
            logger.warning(f"No data available for {symbol}, skipping analysis")
            return None
        
        # Store data in database
        self.store_stock_data(display_symbol, stock_data)
        
        # Get price data for analysis
        prices = [d['close'] for d in stock_data[-analysis_days:] if d['close'] > 0]
        volumes = [d['volume'] for d in stock_data[-analysis_days:]]
        
        if len(prices) < 10:  # Need minimum data for analysis
            logger.warning(f"Insufficient data for {symbol} analysis")
            return None
        
        current_price = prices[-1]
        
        # Calculate price changes based on timeframe
        if len(prices) > 1:
            timeframe_start_price = prices[0]
        else:
            timeframe_start_price = current_price
        
        # Calculate technical indicators
        rsi = self.calculate_rsi(prices)
        macd = self.calculate_macd(prices)
        support, resistance = self.find_support_resistance(prices)
        
        # Calculate potential gain percentage
        potential_gain_percent = self.calculate_potential_gain(current_price, resistance)
        
        # Calculate price changes
        change_amount = current_price - timeframe_start_price
        change_percent = (change_amount / timeframe_start_price) * 100 if timeframe_start_price != 0 else 0
        
        # Calculate volume metrics
        current_volume = volumes[-1] if volumes else 0
        volume_period = min(20, len(volumes))
        avg_volume = sum(volumes[-volume_period:]) / volume_period if volumes else 0
        
        # Determine trading signal
        signal = self.determine_signal(current_price, support, resistance, rsi, macd)
        
        # Calculate risk/reward ratio
        risk = abs(current_price - support) / current_price if support < current_price else 0.01
        reward = abs(resistance - current_price) / current_price if resistance > current_price else 0.01
        risk_reward_ratio = reward / risk if risk > 0 else 1.0
        
        # Calculate composite score with timeframe-specific adjustments
        score = self.calculate_score(signal, rsi, macd, current_volume, avg_volume, risk_reward_ratio, potential_gain_percent, timeframe)
        
        # Store analysis results
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO stock_analysis 
            (symbol, name, sector, timeframe, current_price, change_amount, change_percent,
             support_level, resistance_level, potential_gain_percent, rsi, macd, volume, avg_volume,
             signal, score, risk_reward_ratio, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            display_symbol,
            stock_info['name'],
            stock_info.get('sector', 'Unknown'),
            timeframe,
            round(current_price, 2),
            round(change_amount, 2),
            round(change_percent, 2),
            support,
            resistance,
            potential_gain_percent,
            rsi,
            macd,
            int(current_volume),
            int(avg_volume),
            signal,
            score,
            round(risk_reward_ratio, 2),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        return {
            'symbol': display_symbol,
            'name': stock_info['name'],
            'sector': stock_info.get('sector', 'Unknown'),
            'timeframe': timeframe,
            'timeframeName': self.timeframes.get(timeframe, {'name': timeframe})['name'],
            'currentPrice': round(current_price, 2),
            'change': round(change_amount, 2),
            'changePercent': round(change_percent, 2),
            'support': support,
            'resistance': resistance,
            'potentialGainPercent': potential_gain_percent,
            'rsi': rsi,
            'macd': macd,
            'volume': int(current_volume),
            'avgVolume': int(avg_volume),
            'signal': signal,
            'score': score,
            'riskRewardRatio': round(risk_reward_ratio, 2),
            'lastUpdated': datetime.now().isoformat()
        }
    
    def determine_signal(self, price, support, resistance, rsi, macd):
        """Determine buy/wait/avoid signal based on technical analysis"""
        distance_from_support = (price - support) / support if support > 0 else 1
        distance_from_resistance = (resistance - price) / price if price > 0 else 1
        
        # Buy conditions
        if (distance_from_support < 0.05 and  # Near support
            rsi < 40 and  # Oversold
            macd > 0):  # Positive momentum
            return 'BUY'
        
        # Avoid conditions
        if (distance_from_resistance < 0.05 or  # Near resistance
            rsi > 70):  # Overbought
            return 'AVOID'
        
        return 'WAIT'
    
    def calculate_score(self, signal, rsi, macd, volume, avg_volume, risk_reward_ratio, potential_gain_percent, timeframe):
        """Calculate composite score for stock ranking with timeframe-specific adjustments"""
        score = 50  # Base score
        
        # Signal bonus
        if signal == 'BUY':
            score += 30
        elif signal == 'AVOID':
            score -= 20
        
        # RSI scoring
        if rsi < 30:
            score += 20  # Very oversold
        elif rsi < 40:
            score += 15  # Oversold
        elif rsi > 70:
            score -= 15  # Overbought
        
        # MACD scoring
        if macd > 0:
            score += 10
        
        # Volume scoring
        volume_ratio = volume / avg_volume if avg_volume > 0 else 1
        if volume_ratio > 1.5:
            score += 10  # High volume
        elif volume_ratio < 0.5:
            score -= 5  # Low volume
        
        # Risk/reward scoring
        if risk_reward_ratio > 3:
            score += 20
        elif risk_reward_ratio > 2:
            score += 15
        elif risk_reward_ratio > 1.5:
            score += 10
        
        # Potential gain scoring
        if potential_gain_percent > 20:
            score += 25
        elif potential_gain_percent > 15:
            score += 20
        elif potential_gain_percent > 10:
            score += 15
        elif potential_gain_percent > 5:
            score += 10
        
        # Long-term timeframe specific adjustments
        if timeframe in ['2Y', '3Y', '4Y', '5Y', '10Y']:
            # Long-term: Favor stability and consistent growth
            if 30 < rsi < 70:  # Stable RSI range
                score += 10
            if risk_reward_ratio > 2:  # Good long-term risk/reward
                score += 10
            if potential_gain_percent > 15:  # Higher potential for long-term
                score += 15
            
            # Penalize extreme volatility for long-term investments
            if rsi < 20 or rsi > 80:
                score -= 10
        
        return max(0, min(100, int(score)))
    
    def get_all_stocks_analysis(self, timeframe='1M'):
        """Get analysis for all NIFTY 100 stocks for specified timeframe"""
        results = []
        total_stocks = len(self.nifty_100_stocks)
        
        logger.info(f"Starting analysis for {total_stocks} stocks with {timeframe} timeframe...")
        
        for i, stock in enumerate(self.nifty_100_stocks, 1):
            try:
                logger.info(f"Analyzing {stock['display_symbol']} ({i}/{total_stocks})...")
                analysis = self.analyze_stock(stock, timeframe)
                if analysis:
                    results.append(analysis)
                    logger.info(f"✓ {stock['display_symbol']}: Score {analysis['score']}, Signal {analysis['signal']}")
                else:
                    logger.warning(f"✗ Failed to analyze {stock['display_symbol']}")
                    
                # Small delay to avoid overwhelming the API
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error analyzing {stock['display_symbol']}: {str(e)}")
                continue
        
        # Sort by score (highest first)
        results.sort(key=lambda x: x['score'], reverse=True)
        logger.info(f"Analysis complete! {len(results)} stocks analyzed successfully.")
        
        return results
    
    def get_chart_data(self, symbol, days=30):
        """Get chart data for a specific stock"""
        # Find the stock info
        stock_info = None
        for stock in self.nifty_100_stocks:
            if stock['display_symbol'].upper() == symbol.upper():
                stock_info = stock
                break
        
        if not stock_info:
            return None
        
        # Fetch data from Yahoo Finance with appropriate period for long-term charts
        if days <= 90:
            period = '3mo'
        elif days <= 365:
            period = '1y'
        elif days <= 1825:  # 5 years
            period = '5y'
        else:
            period = 'max'
        
        stock_data = self.fetch_stock_data_yfinance(stock_info['symbol'], period)
        
        if not stock_data:
            return None
        
        # Get the requested number of days
        chart_data = stock_data[-days:] if len(stock_data) > days else stock_data
        
        # Get support and resistance levels
        prices = [d['close'] for d in chart_data]
        support, resistance = self.find_support_resistance(prices)
        
        return {
            'symbol': symbol,
            'data': [
                {
                    'time': d['date'],
                    'open': d['open'],
                    'high': d['high'],
                    'low': d['low'],
                    'close': d['close'],
                    'volume': d['volume']
                }
                for d in chart_data
            ],
            'supportLevels': [support],
            'resistanceLevels': [resistance]
        }
    
    def get_available_timeframes(self):
        """Get list of available timeframes"""
        return [
            {'value': key, 'name': value['name'], 'days': value['days']}
            for key, value in self.timeframes.items()
        ]

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize stock analyzer
analyzer = NSEStockAnalyzer()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'message': 'NSE Stock Analysis Flask API is running',
        'timestamp': datetime.now().isoformat(),
        'version': '3.1.0',
        'data_source': 'Yahoo Finance (Real NSE Data)',
        'supported_timeframes': list(analyzer.timeframes.keys())
    })

@app.route('/api/stocks', methods=['GET'])
def get_stocks():
    """Get all stocks analysis with optional timeframe"""
    try:
        timeframe = request.args.get('timeframe', '1M')
        
        # Validate timeframe
        if timeframe not in analyzer.timeframes:
            return jsonify({
                'success': False,
                'error': f'Invalid timeframe. Supported: {list(analyzer.timeframes.keys())}'
            }), 400
        
        logger.info(f"Fetching stocks analysis for timeframe: {timeframe}")
        stocks = analyzer.get_all_stocks_analysis(timeframe)
        
        return jsonify({
            'success': True,
            'data': stocks,
            'timeframe': timeframe,
            'timestamp': datetime.now().isoformat(),
            'count': len(stocks),
            'data_source': 'Yahoo Finance (Real NSE Data)'
        })
        
    except Exception as e:
        logger.error(f"Error in get_stocks: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/chart', methods=['GET'])
def get_chart():
    """Get chart data for specific stock"""
    try:
        symbol = request.args.get('symbol')
        days = int(request.args.get('days', 30))
        
        if not symbol:
            return jsonify({
                'success': False,
                'error': 'Symbol parameter is required'
            }), 400
        
        # Extended range for long-term analysis
        if days < 1 or days > 3650:  # Up to 10 years
            return jsonify({
                'success': False,
                'error': 'Days must be between 1 and 3650 (10 years)'
            }), 400
        
        chart_data = analyzer.get_chart_data(symbol.upper(), days)
        
        if chart_data:
            return jsonify({
                'success': True,
                'data': chart_data,
                'data_source': 'Yahoo Finance (Real NSE Data)'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Stock data not found'
            }), 404
            
    except ValueError:
        return jsonify({
            'success': False,
            'error': 'Invalid days parameter. Must be a number.'
        }), 400
    except Exception as e:
        logger.error(f"Error in get_chart: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/timeframes', methods=['GET'])
def get_timeframes():
    """Get available timeframes"""
    try:
        timeframes = analyzer.get_available_timeframes()
        
        return jsonify({
            'success': True,
            'data': timeframes
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stock/<symbol>', methods=['GET'])
def get_single_stock(symbol):
    """Get analysis for a single stock"""
    try:
        timeframe = request.args.get('timeframe', '1M')
        
        # Validate timeframe
        if timeframe not in analyzer.timeframes:
            return jsonify({
                'success': False,
                'error': f'Invalid timeframe. Supported: {list(analyzer.timeframes.keys())}'
            }), 400
        
        # Find stock info
        stock_info = None
        for stock in analyzer.nifty_100_stocks:
            if stock['display_symbol'].upper() == symbol.upper():
                stock_info = stock
                break
        
        if not stock_info:
            return jsonify({
                'success': False,
                'error': 'Stock not found in NIFTY 100'
            }), 404
        
        analysis = analyzer.analyze_stock(stock_info, timeframe)
        
        if analysis:
            return jsonify({
                'success': True,
                'data': analysis,
                'data_source': 'Yahoo Finance (Real NSE Data)'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to analyze stock'
            }), 500
            
    except Exception as e:
        logger.error(f"Error in get_single_stock: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

if __name__ == '__main__':
    print("🚀 NSE NIFTY 100 Stock Analysis Flask API")
    print("=" * 60)
    print("📊 Features:")
    print("  • Real NSE stock data via Yahoo Finance")
    print("  • Extended timeframe analysis:")
    print("    - Short-term: 1W, 1M, 3M, 6M, 1Y")
    print("    - Long-term: 2Y, 3Y, 4Y, 5Y, 10Y")
    print("  • Technical indicators (RSI, MACD, Support/Resistance)")
    print("  • Trading signals (BUY/WAIT/AVOID)")
    print("  • Potential gain calculations")
    print("  • Risk/reward analysis")
    print("  • Data caching for performance")
    print("  • Long-term investment scoring")
    print()
    print("🌐 API Endpoints:")
    print("  GET /api/health - Health check")
    print("  GET /api/stocks?timeframe=1M - Get all stocks analysis")
    print("  GET /api/stock/<symbol>?timeframe=1M - Get single stock analysis")
    print("  GET /api/chart?symbol=SYMBOL&days=30 - Get chart data")
    print("  GET /api/timeframes - Get available timeframes")
    print()
    print("📈 Data Source: Yahoo Finance (Real NSE Data)")
    print("⏰ Supported Timeframes:", ', '.join(analyzer.timeframes.keys()))
    print("⚡ Starting server on http://localhost:8000")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=8000, debug=True)