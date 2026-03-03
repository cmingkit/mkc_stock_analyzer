"""
Sentiment Analyzer Module
Analyzes sentiment from Reddit data
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from src.analyzers.base_analyzer import BaseAnalyzer
from src.utils.logger import get_logger
from src.utils.stock_info import get_stock_name

log = get_logger("sentiment_analyzer")


class SentimentAnalyzer(BaseAnalyzer):
    """Analyses sentiment from Reddit mentions"""
    
    # Sentiment emoji mapping
    SENTIMENT_EMOJI = {
        'positive': '📈',
        'negative': '📉',
        'neutral': '➡️'
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize sentiment analyzer
        
        Args:
            config: Configuration dictionary with keys:
                - top_stocks: Number of top stocks to analyze
                - risk_threshold: Threshold for high risk (0-1)
        """
        super().__init__(config)
        
        self.top_stocks = self.config.get('top_stocks', 15)
        self.risk_threshold = self.config.get('risk_threshold', 0.7)
    
    def analyze(self, reddit_data: Dict[str, Any], price_data: Optional[Dict[str, Any]] = None, *args, **kwargs) -> Dict[str, Any]:
        """
        Analyze sentiment from Reddit data
        
        Args:
            reddit_data: Reddit data from RedditCollector
            price_data: Optional price data to enrich stock info
        
        Returns:
            Sentiment analysis results
        """
        log.info("=" * 60)
        log.info("Analyzing Reddit sentiment")
        log.info("=" * 60)
        
        stock_mentions = reddit_data.get('stock_mentions', {})
        
        if not stock_mentions:
            log.warning("No stock mentions to analyze")
            return {'top_stocks': [], 'timestamp': datetime.now().isoformat()}
        
        # Sort by mention count
        sorted_stocks = sorted(
            stock_mentions.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )
        
        # Get price info if available
        prices = {}
        if price_data:
            prices = price_data.get('price_data', {})
        
        # Analyze top stocks
        top_stocks = []
        for ticker, data in sorted_stocks[:self.top_stocks]:
            analysis = self._analyze_stock(ticker, data, prices.get(ticker, {}))
            top_stocks.append(analysis)
        
        self._results = {
            'top_stocks': top_stocks,
            'total_mentions': sum(s['count'] for s in stock_mentions.values()),
            'unique_stocks': len(stock_mentions),
            'timestamp': datetime.now().isoformat()
        }
        
        log.info(f"Analyzed {len(top_stocks)} top stocks")
        
        return self._results
    
    def _analyze_stock(self, ticker: str, data: Dict[str, Any], price_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze a single stock's sentiment
        
        Args:
            ticker: Stock ticker
            data: Mention data
            price_info: Optional price information
        
        Returns:
            Stock analysis results
        """
        count = data['count']
        positive = data['positive']
        negative = data['negative']
        neutral = data['neutral']
        total = positive + negative + neutral
        
        # Calculate bull ratio
        bull_ratio = positive / total if total > 0 else 0.5
        
        # Determine sentiment
        if bull_ratio > 0.6:
            sentiment = 'positive'
        elif bull_ratio < 0.4:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        sentiment_emoji = self.SENTIMENT_EMOJI.get(sentiment, '➡️')
        
        # Assess risk
        risk_level = self._assess_risk(bull_ratio, total)
        
        # Generate recommendation
        recommendation = self._generate_recommendation(bull_ratio, risk_level)
        
        # Process posts for display
        posts = self._process_posts(data.get('posts', []))
        
        result = {
            'ticker': ticker,
            'name': get_stock_name(ticker),
            'count': count,
            'positive': positive,
            'negative': negative,
            'neutral': neutral,
            'bull_ratio': bull_ratio,
            'sentiment': sentiment,
            'sentiment_emoji': sentiment_emoji,
            'risk_level': risk_level,
            'recommendation': recommendation,
            'posts': posts[:5]  # Top 5 posts
        }
        
        # Add current price if available
        if price_info and price_info.get('current_price'):
            result['current_price'] = price_info['current_price']
        
        return result
    
    def _assess_risk(self, bull_ratio: float, total_mentions: int) -> str:
        """
        Assess risk level
        
        Args:
            bull_ratio: Ratio of positive sentiment
            total_mentions: Total number of mentions
        
        Returns:
            Risk level string
        """
        # Not enough data
        if total_mentions < 10:
            return "Medium"
        
        # Extreme sentiment = high risk
        if bull_ratio > self.risk_threshold:
            return "High"
        elif bull_ratio > 0.6:
            return "Medium"
        elif bull_ratio < 0.3:
            return "Medium"
        else:
            return "Low"
    
    def _generate_recommendation(self, bull_ratio: float, risk_level: str) -> str:
        """
        Generate recommendation
        
        Args:
            bull_ratio: Ratio of positive sentiment
            risk_level: Risk level
        
        Returns:
            Recommendation string
        """
        if bull_ratio > 0.7:
            return "📈 Strong bullish sentiment - monitor for reversal"
        elif bull_ratio > 0.6:
            return "✅ Bullish sentiment - potential upside"
        elif bull_ratio < 0.3:
            return "📉 Strong bearish sentiment - exercise caution"
        elif bull_ratio < 0.4:
            return "⚠️ Bearish sentiment - wait for signals"
        else:
            return "➡️ Neutral sentiment - monitor developments"
    
    def _process_posts(self, posts: List[Dict]) -> List[Dict]:
        """
        Process posts for display
        
        Args:
            posts: Raw post data
        
        Returns:
            Processed posts list
        """
        processed = []
        
        for post in posts[:10]:
            processed.append({
                'title': post.get('title', '')[:100],  # Limit title length
                'url': post.get('url', ''),
                'sentiment': post.get('sentiment', 'neutral'),
                'sentiment_emoji': self.SENTIMENT_EMOJI.get(post.get('sentiment', 'neutral'), '➡️'),
                'subreddit': post.get('subreddit', 'r/stocks'),
                'confidence': post.get('confidence', 0.5)
            })
        
        return processed
