"""
Price Collector Module
Collects stock price data from various sources
"""

import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import requests

from src.collectors.base_collector import BaseCollector
from src.utils.logger import get_logger
from src.utils.rate_limiter import RateLimiter

log = get_logger("price_collector")

# Try to import yfinance
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    log.warning("yfinance not installed, using alternative data sources")


class PriceCollector(BaseCollector):
    """Collects stock price data"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize price collector
        
        Args:
            config: Configuration dictionary with keys:
                - providers: List of data providers ('yfinance', 'yahoo_api')
                - cache_ttl: Cache time-to-live in seconds
                - yahoo_api_delay: Delay between Yahoo API calls
                - alpha_vantage_api_key: Alpha Vantage API key
        """
        super().__init__(config)
        
        self.providers = self.config.get('providers', ['yfinance'])
        self.cache_ttl = self.config.get('cache_ttl', 3600)
        self.yahoo_api_delay = self.config.get('yahoo_api_delay', 2.0)
        self.alpha_vantage_api_key = self.config.get('alpha_vantage_api_key')
        
        # Rate limiter
        self.rate_limiter = RateLimiter(calls=30, period=60)
        
        # Cache
        self._price_cache: Dict[str, Tuple[float, float]] = {}  # ticker -> (price, timestamp)
        self._history_cache: Dict[str, Tuple[List, float]] = {}  # ticker -> (history, timestamp)
        
        # Last Yahoo API request time
        self._last_yahoo_request: float = 0
    
    def _wait_for_yahoo(self):
        """Wait to respect Yahoo API rate limits"""
        elapsed = time.time() - self._last_yahoo_request
        if elapsed < self.yahoo_api_delay:
            time.sleep(self.yahoo_api_delay - elapsed)
        self._last_yahoo_request = time.time()
    
    def get_current_price(self, ticker: str) -> Optional[float]:
        """
        Get current stock price
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            Current price or None on error
        """
        # Check cache
        if ticker in self._price_cache:
            price, timestamp = self._price_cache[ticker]
            if time.time() - timestamp < self.cache_ttl:
                return price
        
        # Try yfinance first
        if YFINANCE_AVAILABLE and 'yfinance' in self.providers:
            price = self._get_price_yfinance(ticker)
            if price:
                self._price_cache[ticker] = (price, time.time())
                return price
        
        # Fallback to Yahoo API
        if 'yahoo_api' in self.providers:
            price = self._get_price_yahoo_api(ticker)
            if price:
                self._price_cache[ticker] = (price, time.time())
                return price
        
        return None
    
    def _get_price_yfinance(self, ticker: str) -> Optional[float]:
        """Get price using yfinance"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            return info.get('regularMarketPrice') or info.get('currentPrice')
        except Exception as e:
            log.warning(f"yfinance price fetch failed for {ticker}: {e}")
            return None
    
    def _get_price_yahoo_api(self, ticker: str) -> Optional[float]:
        """Get price using Yahoo Finance API"""
        self._wait_for_yahoo()
        
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=1d"
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                result = data['chart']['result'][0]
                meta = result.get('meta', {})
                return meta.get('regularMarketPrice')
            
            return None
        except Exception as e:
            log.warning(f"Yahoo API price fetch failed for {ticker}: {e}")
            return None
    
    def get_history(self, ticker: str, days: int = 90) -> List[Tuple[datetime, float]]:
        """
        Get historical price data
        
        Args:
            ticker: Stock ticker symbol
            days: Number of days of history
        
        Returns:
            List of (date, price) tuples
        """
        cache_key = f"{ticker}_{days}"
        
        # Check cache
        if cache_key in self._history_cache:
            history, timestamp = self._history_cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return history
        
        # Try yfinance first
        if YFINANCE_AVAILABLE and 'yfinance' in self.providers:
            history = self._get_history_yfinance(ticker, days)
            if history:
                self._history_cache[cache_key] = (history, time.time())
                return history
        
        # Fallback to Yahoo API
        if 'yahoo_api' in self.providers:
            history = self._get_history_yahoo_api(ticker, days)
            if history:
                self._history_cache[cache_key] = (history, time.time())
                return history
        
        return []
    
    def _get_history_yfinance(self, ticker: str, days: int) -> List[Tuple[datetime, float]]:
        """Get history using yfinance"""
        try:
            stock = yf.Ticker(ticker)
            period = "3mo" if days >= 90 else "1mo"
            hist = stock.history(period=period)
            
            if hist.empty or len(hist) < 20:
                return []
            
            history = []
            for index, row in hist.iterrows():
                history.append((index.to_pydatetime(), row['Close']))
            
            return history
        except Exception as e:
            log.warning(f"yfinance history fetch failed for {ticker}: {e}")
            return []
    
    def _get_history_yahoo_api(self, ticker: str, days: int) -> List[Tuple[datetime, float]]:
        """Get history using Yahoo Finance API"""
        self._wait_for_yahoo()
        
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range={days}d"
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                result = data['chart']['result'][0]
                timestamps = result.get('timestamp', [])
                indicators = result.get('indicators', {})
                quotes = indicators.get('quote', [{}])[0]
                closes = quotes.get('close', [])
                
                history = [
                    (datetime.fromtimestamp(ts), close)
                    for ts, close in zip(timestamps, closes)
                    if close is not None
                ]
                
                return history
            
            return []
        except Exception as e:
            log.warning(f"Yahoo API history fetch failed for {ticker}: {e}")
            return []
    
    def collect(self, tickers: List[str], days: int = 90) -> Dict[str, Any]:
        """
        Collect price data for multiple tickers
        
        Args:
            tickers: List of ticker symbols
            days: Number of days of history
        
        Returns:
            Dictionary with price data
        """
        log.info("=" * 60)
        log.info(f"Collecting price data for {len(tickers)} stocks")
        log.info("=" * 60)
        
        price_data = {}
        
        for ticker in tickers:
            log.info(f"Fetching data for {ticker}...")
            
            current_price = self.get_current_price(ticker)
            history = self.get_history(ticker, days)
            
            price_data[ticker] = {
                'current_price': current_price,
                'history': history,
                'history_days': len(history)
            }
            
            if current_price:
                log.info(f"  {ticker}: ${current_price:.2f}")
            else:
                log.warning(f"  {ticker}: Price unavailable")
        
        self._data = {
            'price_data': price_data,
            'timestamp': datetime.now().isoformat(),
            'tickers_collected': len(price_data)
        }
        
        return self._data
    
    def clear_cache(self):
        """Clear price and history caches"""
        self._price_cache.clear()
        self._history_cache.clear()
        log.info("Price cache cleared")
