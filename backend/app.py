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
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NSEStockAnalyzer:
    def __init__(self):
        self.db_path = 'stocks.db'
        self.init_database()

        # Initialize empty list - will be populated from NSE API
        self.nifty_100_stocks = []

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

        # Cache for NIFTY 100 list (refresh daily)
        self.nifty_list_cache_expiry = None
        self.nifty_list_cache_duration = 86400  # 24 hours

        # Load NIFTY 100 stocks on initialization
        self.load_nifty_100_stocks()

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

        # Create table to cache NIFTY 100 stocks list
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS nifty_100_stocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL UNIQUE,
                display_symbol TEXT NOT NULL,
                name TEXT NOT NULL,
                sector TEXT,
                last_updated TEXT NOT NULL
            )
        ''')

        conn.commit()
        conn.close()

    def fetch_nifty_100_from_nse(self):
        """Fetch NIFTY 100 stocks list from NSE website"""
        try:
            logger.info("Fetching NIFTY 100 stocks list from NSE...")

            # NSE API endpoint for NIFTY 100 constituents
            url = "https://www.niftyindices.com/IndexConstituent/ind_nifty100list.csv"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            # Parse CSV data
            lines = response.text.strip().split('\n')
            stocks = []

            # Skip header line
            for line in lines[1:]:
                if line.strip():
                    parts = line.split(',')
                    if len(parts) >= 3:
                        company_name = parts[0].strip().strip('"')
                        industry = parts[1].strip().strip('"') if len(parts) > 1 else 'Unknown'
                        symbol = parts[2].strip().strip('"')

                        if symbol and company_name:
                            # Clean up symbol and create Yahoo Finance format
                            clean_symbol = symbol.replace('"', '').strip()
                            yahoo_symbol = f"{clean_symbol}.NS"

                            # Map industry to sector
                            sector = self.map_industry_to_sector(industry)

                            stocks.append({
                                'symbol': yahoo_symbol,
                                'display_symbol': clean_symbol,
                                'name': company_name,
                                'sector': sector
                            })

            if len(stocks) < 50:  # Sanity check
                raise Exception(f"Too few stocks fetched: {len(stocks)}. Expected around 100.")

            logger.info(f"Successfully fetched {len(stocks)} NIFTY 100 stocks from NSE")
            return stocks

        except Exception as e:
            logger.error(f"Error fetching NIFTY 100 from NSE: {str(e)}")
            return None

    def fetch_nifty_100_alternative(self):
        """Alternative method to fetch NIFTY 100 using different sources"""
        try:
            logger.info("Trying alternative method to fetch NIFTY 100...")

            # Try NSE India website
            url = "https://archives.nseindia.com/content/indices/ind_nifty100list.csv"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }

            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code == 200:
                lines = response.text.strip().split('\n')
                stocks = []

                for line in lines[1:]:  # Skip header
                    if line.strip():
                        parts = [p.strip().strip('"') for p in line.split(',')]
                        if len(parts) >= 3:
                            company_name = parts[0]
                            industry = parts[1] if len(parts) > 1 else 'Unknown'
                            symbol = parts[2]

                            if symbol and company_name:
                                yahoo_symbol = f"{symbol}.NS"
                                sector = self.map_industry_to_sector(industry)

                                stocks.append({
                                    'symbol': yahoo_symbol,
                                    'display_symbol': symbol,
                                    'name': company_name,
                                    'sector': sector
                                })

                if len(stocks) >= 50:
                    logger.info(f"Alternative method successful: {len(stocks)} stocks")
                    return stocks

            # If still no success, return fallback list
            logger.warning("All API methods failed, using fallback stock list")
            return self.get_fallback_nifty_100()

        except Exception as e:
            logger.error(f"Alternative method failed: {str(e)}")
            return self.get_fallback_nifty_100()

    def get_fallback_nifty_100(self):
        """Fallback NIFTY 100 list in case API fails"""
        logger.info("Using fallback NIFTY 100 stock list")

        # Comprehensive fallback list of major NIFTY 100 stocks
        fallback_stocks = [
            # Banking & Financial Services
            {'symbol': 'HDFCBANK.NS', 'display_symbol': 'HDFCBANK', 'name': 'HDFC Bank Ltd', 'sector': 'Banking'},
            {'symbol': 'ICICIBANK.NS', 'display_symbol': 'ICICIBANK', 'name': 'ICICI Bank Ltd', 'sector': 'Banking'},
            {'symbol': 'SBIN.NS', 'display_symbol': 'SBIN', 'name': 'State Bank of India', 'sector': 'Banking'},
            {'symbol': 'AXISBANK.NS', 'display_symbol': 'AXISBANK', 'name': 'Axis Bank Ltd', 'sector': 'Banking'},
            {'symbol': 'KOTAKBANK.NS', 'display_symbol': 'KOTAKBANK', 'name': 'Kotak Mahindra Bank',
             'sector': 'Banking'},
            {'symbol': 'INDUSINDBK.NS', 'display_symbol': 'INDUSINDBK', 'name': 'IndusInd Bank Ltd',
             'sector': 'Banking'},
            {'symbol': 'BAJFINANCE.NS', 'display_symbol': 'BAJFINANCE', 'name': 'Bajaj Finance Ltd', 'sector': 'NBFC'},
            {'symbol': 'BAJAJFINSV.NS', 'display_symbol': 'BAJAJFINSV', 'name': 'Bajaj Finserv Ltd', 'sector': 'NBFC'},

            # Information Technology
            {'symbol': 'TCS.NS', 'display_symbol': 'TCS', 'name': 'Tata Consultancy Services', 'sector': 'IT'},
            {'symbol': 'INFY.NS', 'display_symbol': 'INFY', 'name': 'Infosys Ltd', 'sector': 'IT'},
            {'symbol': 'HCLTECH.NS', 'display_symbol': 'HCLTECH', 'name': 'HCL Technologies Ltd', 'sector': 'IT'},
            {'symbol': 'WIPRO.NS', 'display_symbol': 'WIPRO', 'name': 'Wipro Ltd', 'sector': 'IT'},
            {'symbol': 'TECHM.NS', 'display_symbol': 'TECHM', 'name': 'Tech Mahindra Ltd', 'sector': 'IT'},
            {'symbol': 'LTI.NS', 'display_symbol': 'LTI', 'name': 'Larsen & Toubro Infotech', 'sector': 'IT'},

            # Oil & Gas
            {'symbol': 'RELIANCE.NS', 'display_symbol': 'RELIANCE', 'name': 'Reliance Industries Ltd',
             'sector': 'Oil & Gas'},
            {'symbol': 'ONGC.NS', 'display_symbol': 'ONGC', 'name': 'Oil & Natural Gas Corp', 'sector': 'Oil & Gas'},
            {'symbol': 'BPCL.NS', 'display_symbol': 'BPCL', 'name': 'Bharat Petroleum Corp Ltd', 'sector': 'Oil & Gas'},
            {'symbol': 'IOC.NS', 'display_symbol': 'IOC', 'name': 'Indian Oil Corp Ltd', 'sector': 'Oil & Gas'},

            # Automobiles
            {'symbol': 'MARUTI.NS', 'display_symbol': 'MARUTI', 'name': 'Maruti Suzuki India Ltd', 'sector': 'Auto'},
            {'symbol': 'M&M.NS', 'display_symbol': 'M&M', 'name': 'Mahindra & Mahindra Ltd', 'sector': 'Auto'},
            {'symbol': 'TATAMOTORS.NS', 'display_symbol': 'TATAMOTORS', 'name': 'Tata Motors Ltd', 'sector': 'Auto'},
            {'symbol': 'HEROMOTOCO.NS', 'display_symbol': 'HEROMOTOCO', 'name': 'Hero MotoCorp Ltd', 'sector': 'Auto'},
            {'symbol': 'BAJAJ-AUTO.NS', 'display_symbol': 'BAJAJ-AUTO', 'name': 'Bajaj Auto Ltd', 'sector': 'Auto'},
            {'symbol': 'EICHERMOT.NS', 'display_symbol': 'EICHERMOT', 'name': 'Eicher Motors Ltd', 'sector': 'Auto'},

            # FMCG
            {'symbol': 'HINDUNILVR.NS', 'display_symbol': 'HINDUNILVR', 'name': 'Hindustan Unilever Ltd',
             'sector': 'FMCG'},
            {'symbol': 'ITC.NS', 'display_symbol': 'ITC', 'name': 'ITC Ltd', 'sector': 'FMCG'},
            {'symbol': 'NESTLEIND.NS', 'display_symbol': 'NESTLEIND', 'name': 'Nestle India Ltd', 'sector': 'FMCG'},
            {'symbol': 'BRITANNIA.NS', 'display_symbol': 'BRITANNIA', 'name': 'Britannia Industries Ltd',
             'sector': 'FMCG'},
            {'symbol': 'DABUR.NS', 'display_symbol': 'DABUR', 'name': 'Dabur India Ltd', 'sector': 'FMCG'},

            # Pharmaceuticals
            {'symbol': 'SUNPHARMA.NS', 'display_symbol': 'SUNPHARMA', 'name': 'Sun Pharmaceutical Industries',
             'sector': 'Pharma'},
            {'symbol': 'DRREDDY.NS', 'display_symbol': 'DRREDDY', 'name': 'Dr Reddys Laboratories', 'sector': 'Pharma'},
            {'symbol': 'CIPLA.NS', 'display_symbol': 'CIPLA', 'name': 'Cipla Ltd', 'sector': 'Pharma'},
            {'symbol': 'DIVISLAB.NS', 'display_symbol': 'DIVISLAB', 'name': 'Divis Laboratories Ltd',
             'sector': 'Pharma'},

            # Metals & Mining
            {'symbol': 'TATASTEEL.NS', 'display_symbol': 'TATASTEEL', 'name': 'Tata Steel Ltd', 'sector': 'Steel'},
            {'symbol': 'JSWSTEEL.NS', 'display_symbol': 'JSWSTEEL', 'name': 'JSW Steel Ltd', 'sector': 'Steel'},
            {'symbol': 'HINDALCO.NS', 'display_symbol': 'HINDALCO', 'name': 'Hindalco Industries Ltd',
             'sector': 'Metals'},
            {'symbol': 'COALINDIA.NS', 'display_symbol': 'COALINDIA', 'name': 'Coal India Ltd', 'sector': 'Mining'},
            {'symbol': 'VEDL.NS', 'display_symbol': 'VEDL', 'name': 'Vedanta Ltd', 'sector': 'Metals'},

            # Telecom
            {'symbol': 'BHARTIARTL.NS', 'display_symbol': 'BHARTIARTL', 'name': 'Bharti Airtel Ltd',
             'sector': 'Telecom'},

            # Cement
            {'symbol': 'ULTRACEMCO.NS', 'display_symbol': 'ULTRACEMCO', 'name': 'UltraTech Cement Ltd',
             'sector': 'Cement'},
            {'symbol': 'GRASIM.NS', 'display_symbol': 'GRASIM', 'name': 'Grasim Industries Ltd', 'sector': 'Cement'},
            {'symbol': 'SHREECEM.NS', 'display_symbol': 'SHREECEM', 'name': 'Shree Cement Ltd', 'sector': 'Cement'},

            # Power & Utilities
            {'symbol': 'NTPC.NS', 'display_symbol': 'NTPC', 'name': 'NTPC Ltd', 'sector': 'Power'},
            {'symbol': 'POWERGRID.NS', 'display_symbol': 'POWERGRID', 'name': 'Power Grid Corp of India',
             'sector': 'Power'},

            # Infrastructure & Engineering
            {'symbol': 'LT.NS', 'display_symbol': 'LT', 'name': 'Larsen & Toubro Ltd', 'sector': 'Engineering'},
            {'symbol': 'ADANIPORTS.NS', 'display_symbol': 'ADANIPORTS', 'name': 'Adani Ports & SEZ Ltd',
             'sector': 'Infrastructure'},

            # Paints & Chemicals
            {'symbol': 'ASIANPAINT.NS', 'display_symbol': 'ASIANPAINT', 'name': 'Asian Paints Ltd', 'sector': 'Paints'},

            # Consumer Durables
            {'symbol': 'TITAN.NS', 'display_symbol': 'TITAN', 'name': 'Titan Company Ltd',
             'sector': 'Consumer Durables'},
        ]

        return fallback_stocks

    def map_industry_to_sector(self, industry):
        """Map NSE industry classification to broader sectors"""
        industry_lower = industry.lower()

        sector_mapping = {
            'bank': 'Banking',
            'financial': 'Banking',
            'insurance': 'Insurance',
            'information technology': 'IT',
            'software': 'IT',
            'it': 'IT',
            'computer': 'IT',
            'oil': 'Oil & Gas',
            'gas': 'Oil & Gas',
            'petroleum': 'Oil & Gas',
            'automobile': 'Auto',
            'auto': 'Auto',
            'motor': 'Auto',
            'pharmaceutical': 'Pharma',
            'pharma': 'Pharma',
            'drug': 'Pharma',
            'steel': 'Steel',
            'metal': 'Metals',
            'mining': 'Mining',
            'coal': 'Mining',
            'cement': 'Cement',
            'construction': 'Construction',
            'engineering': 'Engineering',
            'power': 'Power',
            'electricity': 'Power',
            'telecom': 'Telecom',
            'telecommunication': 'Telecom',
            'fmcg': 'FMCG',
            'consumer': 'FMCG',
            'food': 'FMCG',
            'paint': 'Paints',
            'chemical': 'Chemicals',
            'textile': 'Textiles',
            'real estate': 'Real Estate',
            'media': 'Media',
            'entertainment': 'Media'
        }

        for keyword, sector in sector_mapping.items():
            if keyword in industry_lower:
                return sector

        return 'Others'

    def load_nifty_100_stocks(self):
        """Load NIFTY 100 stocks from cache or fetch from API"""
        try:
            # Check if we have cached data that's still valid
            if (self.nifty_list_cache_expiry and
                    datetime.now() < self.nifty_list_cache_expiry):

                # Load from database cache
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute('SELECT symbol, display_symbol, name, sector FROM nifty_100_stocks')
                cached_stocks = cursor.fetchall()
                conn.close()

                if cached_stocks:
                    self.nifty_100_stocks = [
                        {
                            'symbol': row[0],
                            'display_symbol': row[1],
                            'name': row[2],
                            'sector': row[3] or 'Unknown'
                        }
                        for row in cached_stocks
                    ]
                    logger.info(f"Loaded {len(self.nifty_100_stocks)} stocks from cache")
                    return

            # Fetch fresh data from NSE
            stocks = self.fetch_nifty_100_from_nse()

            if not stocks:
                # Try alternative method
                stocks = self.fetch_nifty_100_alternative()

            if stocks:
                self.nifty_100_stocks = stocks
                self.cache_nifty_100_stocks(stocks)
                logger.info(f"Successfully loaded {len(stocks)} NIFTY 100 stocks")
            else:
                logger.error("Failed to load NIFTY 100 stocks from all sources")

        except Exception as e:
            logger.error(f"Error loading NIFTY 100 stocks: {str(e)}")
            # Use fallback if everything fails
            self.nifty_100_stocks = self.get_fallback_nifty_100()

    def cache_nifty_100_stocks(self, stocks):
        """Cache NIFTY 100 stocks in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Clear existing cache
            cursor.execute('DELETE FROM nifty_100_stocks')

            # Insert new data
            for stock in stocks:
                cursor.execute('''
                    INSERT INTO nifty_100_stocks 
                    (symbol, display_symbol, name, sector, last_updated)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    stock['symbol'],
                    stock['display_symbol'],
                    stock['name'],
                    stock['sector'],
                    datetime.now().isoformat()
                ))

            conn.commit()
            conn.close()

            # Update cache expiry
            self.nifty_list_cache_expiry = datetime.now() + timedelta(seconds=self.nifty_list_cache_duration)

            logger.info(f"Cached {len(stocks)} NIFTY 100 stocks")

        except Exception as e:
            logger.error(f"Error caching NIFTY 100 stocks: {str(e)}")

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
            change = prices[i] - prices[i - 1]
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
            is_support = all(prices[i] <= prices[j] for j in range(i - window, i + window + 1) if j != i)
            if is_support:
                supports.append(prices[i])

            # Check if current price is a local maximum (resistance)
            is_resistance = all(prices[i] >= prices[j] for j in range(i - window, i + window + 1) if j != i)
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
        score = self.calculate_score(signal, rsi, macd, current_volume, avg_volume, risk_reward_ratio,
                                     potential_gain_percent, timeframe)

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

    def calculate_score(self, signal, rsi, macd, volume, avg_volume, risk_reward_ratio, potential_gain_percent,
                        timeframe):
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
        # Refresh NIFTY 100 list if cache expired
        if (not self.nifty_list_cache_expiry or
                datetime.now() >= self.nifty_list_cache_expiry):
            logger.info("NIFTY 100 cache expired, refreshing...")
            self.load_nifty_100_stocks()

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

    def refresh_nifty_100_list(self):
        """Manually refresh NIFTY 100 stocks list"""
        logger.info("Manually refreshing NIFTY 100 stocks list...")
        self.nifty_list_cache_expiry = None  # Force refresh
        self.load_nifty_100_stocks()
        return len(self.nifty_100_stocks)

    def get_fundamental_data(self, symbol):
        """Get fundamental analysis data for a stock"""
        try:
            # Find the stock info first
            stock_info = None
            for stock in self.nifty_100_stocks:
                if stock['display_symbol'].upper() == symbol.upper():
                    stock_info = stock
                    break

            if not stock_info:
                return None

            logger.info(f"Fetching fundamental data for {symbol}...")

            # Create ticker object
            ticker = yf.Ticker(stock_info['symbol'])

            # Get company info and financial data
            info = ticker.info

            # Helper function to safely get values from info dict
            def safe_get(key, default=None):
                value = info.get(key, default)
                # Handle NaN and infinite values
                if value is not None and isinstance(value, (int, float)):
                    if math.isnan(value) or math.isinf(value):
                        return default
                return value

            # Extract key financial metrics with proper validation
            market_cap = safe_get('marketCap')
            pe_ratio = safe_get('trailingPE')
            pb_ratio = safe_get('priceToBook')
            dividend_yield = safe_get('dividendYield')
            roe = safe_get('returnOnEquity')
            profit_margin = safe_get('profitMargins')
            revenue_growth = safe_get('revenueGrowth')
            book_value = safe_get('bookValue')
            eps = safe_get('trailingEps')
            beta = safe_get('beta')
            fifty_two_week_high = safe_get('fiftyTwoWeekHigh')
            fifty_two_week_low = safe_get('fiftyTwoWeekLow')
            current_ratio = safe_get('currentRatio')

            # Calculate debt-to-equity ratio with improved logic
            total_debt = safe_get('totalDebt', 0)
            total_cash = safe_get('totalCash', 0)
            net_debt = max(0, total_debt - total_cash) if total_debt and total_cash else total_debt

            # Try multiple equity fields for better accuracy
            shareholders_equity = (
                safe_get('totalStockholderEquity') or
                safe_get('stockholdersEquity') or
                safe_get('shareholderEquity') or
                safe_get('bookValue', 0) * safe_get('sharesOutstanding', 0) if safe_get('bookValue') and safe_get(
                    'sharesOutstanding') else None
            )

            debt_to_equity = None
            if shareholders_equity and shareholders_equity > 0 and net_debt is not None:
                debt_to_equity = net_debt / shareholders_equity
            elif total_debt and shareholders_equity and shareholders_equity > 0:
                debt_to_equity = total_debt / shareholders_equity

            # Generate key insights based on the metrics
            key_metrics = []

            # Valuation insights
            if pe_ratio:
                if pe_ratio < 15:
                    key_metrics.append("📈 Undervalued - P/E ratio below 15 suggests good value")
                elif pe_ratio > 30:
                    key_metrics.append("⚠️ Overvalued - High P/E ratio indicates premium pricing")
                else:
                    key_metrics.append("📊 Fairly valued - P/E ratio in reasonable range")

            # Profitability insights
            if roe:
                roe_percent = roe * 100
                if roe_percent > 20:
                    key_metrics.append("🏆 Excellent profitability - ROE above 20%")
                elif roe_percent > 15:
                    key_metrics.append("✅ Good profitability - Strong return on equity")
                elif roe_percent < 10:
                    key_metrics.append("📉 Low profitability - ROE below 10%")

            # Debt analysis with improved logic
            if debt_to_equity is not None:
                if debt_to_equity < 0.3:
                    key_metrics.append("🏦 Low debt levels - financially stable")
                elif debt_to_equity < 0.6:
                    key_metrics.append("📊 Moderate debt levels - manageable")
                elif debt_to_equity < 1.0:
                    key_metrics.append("⚠️ Elevated debt levels - monitor closely")
                else:
                    key_metrics.append("🚨 High debt levels - higher financial risk")
            else:
                key_metrics.append("❓ Debt information not available")

            # Growth insights
            if revenue_growth:
                growth_percent = revenue_growth * 100
                if growth_percent > 15:
                    key_metrics.append("🚀 Strong revenue growth - expanding business")
                elif growth_percent > 5:
                    key_metrics.append("📈 Steady revenue growth")
                elif growth_percent < 0:
                    key_metrics.append("📉 Revenue declining - challenging period")

            # Dividend insights
            if dividend_yield:
                yield_percent = dividend_yield * 100
                if yield_percent > 4:
                    key_metrics.append("💰 High dividend yield - good for income investors")
                elif yield_percent > 2:
                    key_metrics.append("💵 Decent dividend yield")

            # Market position insights
            if market_cap:
                if market_cap > 1000000000000:  # > 1 lakh crore
                    key_metrics.append("🏢 Large-cap stock - established market leader")
                elif market_cap > 100000000000:  # > 10,000 crore
                    key_metrics.append("🏭 Mid-to-large cap - growing company")

            # Volatility insights
            if beta:
                if beta > 1.5:
                    key_metrics.append("📊 High volatility - beta above 1.5")
                elif beta < 0.8:
                    key_metrics.append("🛡️ Low volatility - defensive stock")

            return {
                'symbol': symbol,
                'marketCap': market_cap,
                'peRatio': pe_ratio,
                'pbRatio': pb_ratio,
                'dividendYield': dividend_yield,
                'roe': roe,
                'debtToEquity': debt_to_equity,
                'currentRatio': current_ratio,
                'revenueGrowth': revenue_growth,
                'profitMargin': profit_margin,
                'bookValue': book_value,
                'eps': eps,
                'beta': beta,
                'fiftyTwoWeekHigh': fifty_two_week_high,
                'fiftyTwoWeekLow': fifty_two_week_low,
                'businessSummary': safe_get('longBusinessSummary', ''),
                'keyMetrics': key_metrics,
                'industry': safe_get('industry', ''),
                'sector': safe_get('sector', ''),
                'employees': safe_get('fullTimeEmployees'),
                'website': safe_get('website', ''),
                'lastUpdated': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error fetching fundamental data for {symbol}: {str(e)}")
            return None


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
        'version': '4.0.0',
        'data_source': 'Yahoo Finance (Real NSE Data)',
        'supported_timeframes': list(analyzer.timeframes.keys()),
        'nifty_100_stocks_count': len(analyzer.nifty_100_stocks),
        'last_nifty_refresh': analyzer.nifty_list_cache_expiry.isoformat() if analyzer.nifty_list_cache_expiry else 'Never'
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
            'data_source': 'Yahoo Finance (Real NSE Data)',
            'nifty_100_source': 'NSE API (Dynamic)'
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


@app.route('/api/fundamentals/<symbol>', methods=['GET'])
def get_fundamentals(symbol):
    """Get fundamental analysis for a specific stock"""
    try:
        logger.info(f"Fetching fundamentals for {symbol}")

        fundamental_data = analyzer.get_fundamental_data(symbol.upper())

        if fundamental_data:
            return jsonify({
                'success': True,
                'data': fundamental_data,
                'data_source': 'Yahoo Finance (Real NSE Data)'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Stock not found or fundamental data unavailable'
            }), 404

    except Exception as e:
        logger.error(f"Error in get_fundamentals: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/refresh-nifty', methods=['POST'])
def refresh_nifty_list():
    """Manually refresh NIFTY 100 stocks list"""
    try:
        count = analyzer.refresh_nifty_100_list()

        return jsonify({
            'success': True,
            'message': f'NIFTY 100 stocks list refreshed successfully',
            'stocks_count': count,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error refreshing NIFTY 100 list: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/nifty-stocks', methods=['GET'])
def get_nifty_stocks_list():
    """Get current NIFTY 100 stocks list"""
    try:
        return jsonify({
            'success': True,
            'data': analyzer.nifty_100_stocks,
            'count': len(analyzer.nifty_100_stocks),
            'last_updated': analyzer.nifty_list_cache_expiry.isoformat() if analyzer.nifty_list_cache_expiry else 'Never',
            'data_source': 'NSE API (Dynamic)'
        })

    except Exception as e:
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
    print("=" * 70)
    print("📊 Features:")
    print("  • Dynamic NIFTY 100 stocks list from NSE API")
    print("  • Real NSE stock data via Yahoo Finance")
    print("  • Extended timeframe analysis:")
    print("    - Short-term: 1W, 1M, 3M, 6M, 1Y")
    print("    - Long-term: 2Y, 3Y, 4Y, 5Y, 10Y")
    print("  • Technical indicators (RSI, MACD, Support/Resistance)")
    print("  • Trading signals (BUY/WAIT/AVOID)")
    print("  • Potential gain calculations")
    print("  • Risk/reward analysis")
    print("  • Fundamental analysis with key insights")
    print("  • Data caching for performance")
    print("  • Long-term investment scoring")
    print("  • Automatic daily refresh of NIFTY 100 list")
    print()
    print("🌐 API Endpoints:")
    print("  GET /api/health - Health check")
    print("  GET /api/stocks?timeframe=1M - Get all stocks analysis")
    print("  GET /api/stock/<symbol>?timeframe=1M - Get single stock analysis")
    print("  GET /api/chart?symbol=SYMBOL&days=30 - Get chart data")
    print("  GET /api/fundamentals/<symbol> - Get fundamental analysis")
    print("  GET /api/timeframes - Get available timeframes")
    print("  GET /api/nifty-stocks - Get current NIFTY 100 list")
    print("  POST /api/refresh-nifty - Manually refresh NIFTY 100 list")
    print()
    print("📈 Data Sources:")
    print("  • NIFTY 100 List: NSE API (Dynamic)")
    print("  • Stock Prices: Yahoo Finance (Real NSE Data)")
    print("  • Fundamentals: Yahoo Finance (Real Company Data)")
    print("⏰ Supported Timeframes:", ', '.join(analyzer.timeframes.keys()))
    print(f"📋 NIFTY 100 Stocks Loaded: {len(analyzer.nifty_100_stocks)}")
    print("⚡ Starting server on http://localhost:8000")
    print("=" * 70)

    app.run(host='0.0.0.0', port=8000, debug=True)