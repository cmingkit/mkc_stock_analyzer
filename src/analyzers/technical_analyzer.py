"""
Technical Analyzer Module
Performs technical analysis on stock price data
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from src.analyzers.base_analyzer import BaseAnalyzer
from src.utils.logger import get_logger

log = get_logger("technical_analyzer")


class TechnicalAnalyzer(BaseAnalyzer):
    """Performs technical analysis on stock data"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize technical analyzer
        
        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
    
    def analyze(self, price_data: Dict[str, Any], *args, **kwargs) -> Dict[str, Any]:
        """
        Analyze price data
        
        Args:
            price_data: Price data from PriceCollector
        
        Returns:
            Technical analysis results
        """
        log.info("=" * 60)
        log.info("Performing technical analysis")
        log.info("=" * 60)
        
        analysis_results = {}
        
        for ticker, data in price_data.get('price_data', {}).items():
            history = data.get('history', [])
            
            if len(history) < 20:
                log.warning(f"Insufficient data for {ticker} ({len(history)} days)")
                continue
            
            analysis = self._analyze_stock(ticker, history)
            analysis_results[ticker] = analysis
        
        self._results = {
            'analysis': analysis_results,
            'timestamp': datetime.now().isoformat()
        }
        
        log.info(f"Analyzed {len(analysis_results)} stocks")
        
        return self._results
    
    def _analyze_stock(self, ticker: str, history: List[Tuple[datetime, float]]) -> Dict[str, Any]:
        """
        Analyze a single stock
        
        Args:
            ticker: Stock ticker
            history: Historical price data
        
        Returns:
            Technical analysis results
        """
        prices = [h[1] for h in history]
        current_price = prices[-1]
        
        # Calculate SMAs
        sma_20 = self._calculate_sma(prices, 20)
        sma_50 = self._calculate_sma(prices, 50) if len(prices) >= 50 else None
        
        # Calculate EMAs
        ema_12 = self._calculate_ema(prices, 12)
        ema_26 = self._calculate_ema(prices, 26) if len(prices) >= 26 else None
        
        # Calculate volatility
        volatility = self._calculate_volatility(prices)
        
        # Calculate RSI
        rsi = self._calculate_rsi(prices, 14)
        
        # Determine oversold/overbought
        oversold = rsi is not None and rsi < 30
        overbought = rsi is not None and rsi > 70
        
        # Calculate price changes
        change_7d = self._calculate_change(prices, 7)
        change_30d = self._calculate_change(prices, 30)
        change_90d = self._calculate_change(prices, 90) if len(prices) >= 90 else None
        
        # Determine trend
        if change_7d is not None:
            if change_7d > 5:
                trend = 'strong_up'
                trend_emoji = '🚀'
            elif change_7d > 2:
                trend = 'up'
                trend_emoji = '📈'
            elif change_7d < -5:
                trend = 'strong_down'
                trend_emoji = '💀'
            elif change_7d < -2:
                trend = 'down'
                trend_emoji = '📉'
            else:
                trend = 'neutral'
                trend_emoji = '➡️'
        else:
            trend = 'neutral'
            trend_emoji = '➡️'
        
        # 52-week position
        price_52w_high = max(prices)
        price_52w_low = min(prices)
        
        if price_52w_high == price_52w_low:
            position_52w = 50
        else:
            position_52w = (current_price - price_52w_low) / (price_52w_high - price_52w_low) * 100
        
        # Price vs SMA analysis
        price_vs_sma20 = None
        if sma_20 and current_price:
            diff_pct = ((current_price - sma_20) / sma_20) * 100
            if diff_pct > 0:
                price_vs_sma20 = f"Above SMA20 (+{diff_pct:.1f}%)"
            else:
                price_vs_sma20 = f"Below SMA20 ({diff_pct:.1f}%)"
        
        # MACD signal (simplified)
        macd_signal = "Neutral"
        if ema_12 and ema_26:
            if ema_12 > ema_26:
                macd_signal = "Bullish"
            else:
                macd_signal = "Bearish"
        
        # RSI signal text
        if rsi is not None:
            if rsi < 30:
                rsi_signal = "Oversold - potential buy"
            elif rsi > 70:
                rsi_signal = "Overbought - potential sell"
            else:
                rsi_signal = "Neutral"
        else:
            rsi_signal = "N/A"
        
        return {
            'ticker': ticker,
            'current_price': current_price,
            'sma_20': sma_20,
            'sma_50': sma_50,
            'ema_12': ema_12,
            'ema_26': ema_26,
            'volatility': volatility,
            'rsi': rsi,
            'oversold': oversold,
            'overbought': overbought,
            'change_7d': change_7d,
            'change_30d': change_30d,
            'change_90d': change_90d,
            'trend': trend,
            'trend_emoji': trend_emoji,
            'price_52w_high': price_52w_high,
            'price_52w_low': price_52w_low,
            'position_52w': position_52w,
            'price_vs_sma20': price_vs_sma20,
            'macd_signal': macd_signal,
            'rsi_signal': rsi_signal
        }
    
    def _calculate_sma(self, prices: List[float], period: int) -> Optional[float]:
        """Calculate Simple Moving Average"""
        if len(prices) < period:
            return None
        return sum(prices[-period:]) / period
    
    def _calculate_ema(self, prices: List[float], period: int) -> Optional[float]:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return None
        
        multiplier = 2 / (period + 1)
        
        # Start with SMA
        ema = sum(prices[:period]) / period
        
        # Calculate EMA for remaining prices
        for price in prices[period:]:
            ema = (price - ema) * multiplier + ema
        
        return ema
    
    def _calculate_volatility(self, prices: List[float]) -> float:
        """Calculate price volatility (average daily change %)"""
        if len(prices) < 2:
            return 0
        
        changes = [
            abs((prices[i] - prices[i-1]) / prices[i-1] * 100)
            for i in range(1, len(prices))
        ]
        
        return sum(changes) / len(changes) if changes else 0
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> Optional[float]:
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            return None
        
        gains = []
        losses = []
        
        for i in range(1, period + 1):
            change = prices[-i] - prices[-i-1]
            if change > 0:
                gains.append(change)
            else:
                losses.append(abs(change))
        
        avg_gain = sum(gains) / period if gains else 0
        avg_loss = sum(losses) / period if losses else 0
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _calculate_change(self, prices: List[float], days: int) -> Optional[float]:
        """Calculate price change over specified days"""
        if len(prices) < days + 1:
            return None
        
        return (prices[-1] - prices[-days-1]) / prices[-days-1] * 100
