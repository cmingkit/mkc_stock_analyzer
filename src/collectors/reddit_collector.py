"""
Reddit Collector Module
Collects stock mentions from Reddit subreddits
"""

import re
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

import requests

from src.collectors.base_collector import BaseCollector
from src.utils.logger import get_logger
from src.utils.rate_limiter import RateLimiter

log = get_logger("reddit_collector")


class RedditCollector(BaseCollector):
    """Collects stock mentions from Reddit"""
    
    # Default subreddits to monitor
    DEFAULT_SUBREDDITS = [
        "wallstreetbets", "stocks", "stockmarket", "investing",
        "personalfinance", "ValueInvesting", "Dividends", "Dividends_Equities",
        "Daytrading", "Options", "OptionsTrading", "wealthy", "PassiveIncome", "Millionaires"
    ]
    
    # Default positive sentiment keywords
    DEFAULT_POSITIVE_KEYWORDS = {
        'moon', 'rocket', 'bullish', 'buy', 'go', 'up', 'rise', 'profit',
        'gain', 'win', 'growth', 'explosion', 'surge', 'breakout', 'record',
        'high', 'hit', 'new', 'strong', 'power', 'major', 'bull',
        'stabilize', 'stabilizing', 'recovery', 'recover', 'bounce',
        'lift', 'elevate', 'positive', 'optimistic'
    }
    
    # Default negative sentiment keywords
    DEFAULT_NEGATIVE_KEYWORDS = {
        'dump', 'bearish', 'sell', 'down', 'drop', 'loss', 'crash', 'collapse',
        'plunge', 'panic', 'fear', 'low', 'bad', 'worse', 'worsening',
        'bear', 'short', 'shorting', 'fall', 'decline', 'declining',
        'slump', 'slide'
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Reddit collector
        
        Args:
            config: Configuration dictionary with keys:
                - subreddits: List of subreddits to monitor
                - hot_posts_limit: Number of hot posts to fetch per subreddit
                - rate_limit_delay: Delay between API calls
                - known_stocks: Set of known stock symbols
                - positive_keywords: Set of positive sentiment keywords
                - negative_keywords: Set of negative sentiment keywords
                - reddit_client_id: Reddit OAuth client ID
                - reddit_client_secret: Reddit OAuth client secret
                - reddit_user_agent: Reddit API user agent
        """
        super().__init__(config)
        
        self.subreddits = self.config.get('subreddits', self.DEFAULT_SUBREDDITS)
        self.hot_posts_limit = self.config.get('hot_posts_limit', 30)
        self.rate_limit_delay = self.config.get('rate_limit_delay', 1.0)
        self.known_stocks = self.config.get('known_stocks', set())
        
        self.positive_keywords = self.config.get('positive_keywords', self.DEFAULT_POSITIVE_KEYWORDS)
        self.negative_keywords = self.config.get('negative_keywords', self.DEFAULT_NEGATIVE_KEYWORDS)
        
        # Reddit OAuth configuration
        self.client_id = self.config.get('reddit_client_id')
        self.client_secret = self.config.get('reddit_client_secret')
        self.user_agent = self.config.get('reddit_user_agent', 'StockMonitorBot/1.0')
        
        # OAuth token cache
        self._access_token: Optional[str] = None
        self._token_expires: float = 0
        
        # Rate limiter
        self.rate_limiter = RateLimiter(calls=30, period=60)
        
        # Max workers for parallel processing
        self.max_workers = self.config.get('max_workers', 5)
    
    def _get_access_token(self) -> Optional[str]:
        """Get Reddit OAuth access token"""
        # Check if token is still valid
        if self._access_token and time.time() < self._token_expires:
            return self._access_token
        
        # Check if credentials are configured
        if not all([self.client_id, self.client_secret]):
            log.warning("Reddit OAuth credentials not configured, using unauthenticated mode")
            return None
        
        try:
            auth = requests.auth.HTTPBasicAuth(self.client_id, self.client_secret)
            headers = {'User-Agent': self.user_agent}
            data = {'grant_type': 'client_credentials'}
            
            response = requests.post(
                'https://www.reddit.com/api/v1/access_token',
                auth=auth,
                data=data,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            token_data = response.json()
            self._access_token = token_data['access_token']
            self._token_expires = time.time() + token_data['expires_in'] - 60
            
            log.info("Reddit OAuth token obtained successfully")
            return self._access_token
            
        except Exception as e:
            log.error(f"Reddit OAuth authentication failed: {e}")
            return None
    
    def _fetch_posts(self, subreddit: str) -> Optional[Dict]:
        """
        Fetch hot posts from a subreddit
        
        Args:
            subreddit: Subreddit name
        
        Returns:
            JSON response or None on error
        """
        token = self._get_access_token()
        
        if token:
            url = f"https://oauth.reddit.com/r/{subreddit}/hot.json?limit={self.hot_posts_limit}"
            headers = {
                'User-Agent': self.user_agent,
                'Authorization': f'bearer {token}'
            }
        else:
            url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={self.hot_posts_limit}"
            headers = {'User-Agent': self.user_agent}
        
        try:
            self.rate_limiter.wait()
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                log.error(f"Access forbidden for r/{subreddit}: {e}")
            else:
                log.error(f"HTTP error for r/{subreddit}: {e}")
            return None
        except Exception as e:
            log.error(f"Failed to fetch r/{subreddit}: {e}")
            return None
    
    def _extract_tickers(self, text: str) -> Set[str]:
        """
        Extract stock tickers from text
        
        Args:
            text: Text to extract tickers from
        
        Returns:
            Set of ticker symbols
        """
        # Match $SYMBOL or standalone uppercase words (2-5 chars)
        pattern = r'\$[A-Z]{1,5}\b|\b[A-Z]{2,5}\b'
        tickers = re.findall(pattern, text)
        
        # Clean up
        tickers = {t.replace('$', '').strip() for t in tickers}
        
        # Filter to known stocks if configured
        if self.known_stocks:
            tickers = tickers & self.known_stocks
        
        return tickers
    
    def _analyze_sentiment(self, text: str) -> tuple:
        """
        Analyze sentiment of text
        
        Args:
            text: Text to analyze
        
        Returns:
            Tuple of (sentiment, confidence)
        """
        text_lower = text.lower()
        words = set(text_lower.split())
        
        positive_count = len(words & self.positive_keywords)
        negative_count = len(words & self.negative_keywords)
        
        if positive_count > negative_count:
            return 'positive', positive_count / (positive_count + negative_count + 1)
        elif negative_count > positive_count:
            return 'negative', negative_count / (positive_count + negative_count + 1)
        else:
            return 'neutral', 0.5
    
    def _process_subreddit(self, subreddit: str) -> Dict[str, Any]:
        """
        Process a single subreddit
        
        Args:
            subreddit: Subreddit name
        
        Returns:
            Dictionary of stock mentions
        """
        log.info(f"Monitoring r/{subreddit}...")
        data = self._fetch_posts(subreddit)
        
        if not data or 'data' not in data or 'children' not in data['data']:
            return {}
        
        mentions = defaultdict(lambda: {
            'count': 0,
            'positive': 0,
            'negative': 0,
            'neutral': 0,
            'posts': []
        })
        
        for post in data['data']['children']:
            post_data = post['data']
            title = post_data.get('title', '')
            selftext = post_data.get('selftext', '')
            combined_text = f"{title} {selftext}"
            
            # Extract tickers
            tickers = self._extract_tickers(combined_text)
            
            # Analyze sentiment
            sentiment, confidence = self._analyze_sentiment(combined_text)
            
            for ticker in tickers:
                mentions[ticker]['count'] += 1
                mentions[ticker][sentiment] += 1
                mentions[ticker]['posts'].append({
                    'title': title,
                    'url': f"https://reddit.com{post_data.get('permalink', '')}",
                    'sentiment': sentiment,
                    'confidence': confidence
                })
        
        # Rate limit delay
        time.sleep(self.rate_limit_delay)
        
        return dict(mentions)
    
    def collect(self, subreddits: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Collect stock mentions from Reddit
        
        Args:
            subreddits: List of subreddits to monitor (optional)
        
        Returns:
            Dictionary with stock mentions data
        """
        subreddits = subreddits or self.subreddits
        
        log.info("=" * 60)
        log.info("Reddit Monitoring (Parallel Processing)")
        log.info("=" * 60)
        
        stock_mentions = defaultdict(lambda: {
            'count': 0,
            'positive': 0,
            'negative': 0,
            'neutral': 0,
            'posts': []
        })
        
        # Process subreddits in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._process_subreddit, sub): sub 
                for sub in subreddits
            }
            
            for future in as_completed(futures):
                local_mentions = future.result()
                for ticker, data in local_mentions.items():
                    stock_mentions[ticker]['count'] += data['count']
                    stock_mentions[ticker]['positive'] += data['positive']
                    stock_mentions[ticker]['negative'] += data['negative']
                    stock_mentions[ticker]['neutral'] += data['neutral']
                    stock_mentions[ticker]['posts'].extend(data['posts'])
        
        self._data = {
            'stock_mentions': dict(stock_mentions),
            'timestamp': datetime.now().isoformat(),
            'subreddits_monitored': subreddits,
            'total_stocks_found': len(stock_mentions)
        }
        
        log.info(f"Found {len(stock_mentions)} stocks mentioned")
        
        return self._data
