"""
Risk Analyzer Module
Analyzes risk and identifies undervalued stocks
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from src.analyzers.base_analyzer import BaseAnalyzer
from src.utils.logger import get_logger
from src.utils.stock_info import get_stock_name

log = get_logger("risk_analyzer")


class RiskAnalyzer(BaseAnalyzer):
    """Analyses risk and identifies undervalued stocks"""
    
    # Default undervalued stock categories
    DEFAULT_UNDERVALUED_CATEGORIES = {
        'financial', 'energy', 'industrial', 'healthcare', 
        'retail', 'telecom_utility', 'reits', 'auto', 'consumer'
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize risk analyzer
        
        Args:
            config: Configuration dictionary with keys:
                - undervalued_threshold: Score threshold for undervalued stocks
                - oversold_weight: Weight for oversold score
                - neglect_weight: Weight for neglect score
                - technical_weight: Weight for technical score
        """
        super().__init__(config)
        
        self.undervalued_threshold = self.config.get('undervalued_threshold', 60)
        self.oversold_weight = self.config.get('oversold_weight', 0.35)
        self.neglect_weight = self.config.get('neglect_weight', 0.35)
        self.technical_weight = self.config.get('technical_weight', 0.30)
    
    def analyze(
        self, 
        reddit_data: Dict[str, Any], 
        price_data: Dict[str, Any],
        technical_data: Dict[str, Any],
        undervalued_symbols: Optional[Set[str]] = None,
        *args, **kwargs
    ) -> Dict[str, Any]:
        """
        Analyze risk and identify undervalued stocks
        
        Args:
            reddit_data: Reddit data from RedditCollector
            price_data: Price data from PriceCollector
            technical_data: Technical analysis from TechnicalAnalyzer
            undervalued_symbols: Set of symbols to check for undervaluation
        
        Returns:
            Risk analysis results
        """
        log.info("=" * 60)
        log.info("Analyzing risk and undervalued stocks")
        log.info("=" * 60)
        
        stock_mentions = reddit_data.get('stock_mentions', {})
        price_info = price_data.get('price_data', {})
        tech_analysis = technical_data.get('analysis', {})
        
        undervalued_symbols = undervalued_symbols or set()
        
        undervalued_stocks = []
        
        for ticker in undervalued_symbols:
            # Calculate neglect score (based on Reddit discussion)
            neglect_score, neglect_reasons = self._calculate_neglect_score(ticker, stock_mentions)
            
            # Calculate oversold score (based on technicals)
            oversold_score = 0
            oversold_reasons = []
            technical_score = 0
            technical_reasons = []
            
            if ticker in tech_analysis:
                tech = tech_analysis[ticker]
                oversold_score, oversold_reasons = self._calculate_oversold_score(tech)
                technical_score, technical_reasons = self._calculate_technical_strength(tech)
            
            # Combined score
            undervalued_score = (
                oversold_score * self.oversold_weight +
                neglect_score * self.neglect_weight +
                technical_score * self.technical_weight
            )
            
            if undervalued_score >= self.undervalued_threshold:
                stock_data = price_info.get(ticker, {})
                tech = tech_analysis.get(ticker, {})
                
                # Combine all reasons
                all_reasons = neglect_reasons + oversold_reasons + technical_reasons
                
                undervalued_stocks.append({
                    'ticker': ticker,
                    'name': get_stock_name(ticker),
                    'score': undervalued_score,
                    'oversold_score': oversold_score,
                    'neglect_score': neglect_score,
                    'technical_score': technical_score,
                    'current_price': stock_data.get('current_price'),
                    'rsi': tech.get('rsi'),
                    'label': self._get_label(undervalued_score),
                    'reasons': all_reasons[:5]  # Top 5 reasons
                })
        
        # Sort by score
        undervalued_stocks.sort(key=lambda x: x['score'], reverse=True)
        
        self._results = {
            'undervalued_stocks': undervalued_stocks,
            'timestamp': datetime.now().isoformat()
        }
        
        log.info(f"Found {len(undervalued_stocks)} potentially undervalued stocks")
        
        return self._results
    
    def _calculate_neglect_score(self, ticker: str, stock_mentions: Dict) -> tuple:
        """Calculate neglect score (0-100) and reasons"""
        score = 0
        reasons = []
        
        mentions = stock_mentions.get(ticker, {}).get('count', 0)
        
        if mentions == 0:
            score += 50  # Completely neglected
            reasons.append("No recent social media discussion")
        elif mentions < 3:
            score += 40
            reasons.append("Very low social media attention")
        elif mentions < 5:
            score += 30
            reasons.append("Below-average discussion volume")
        elif mentions < 10:
            score += 20
            reasons.append("Moderate discussion volume")
        
        # Bonus for being in undervalued category
        score += 50
        
        return min(score, 100), reasons
    
    def _calculate_oversold_score(self, tech: Dict) -> tuple:
        """Calculate oversold score (0-100) and reasons"""
        score = 0
        reasons = []
        
        current_price = tech.get('current_price', 0)
        position_52w = tech.get('position_52w', 50)
        rsi = tech.get('rsi')
        sma_20 = tech.get('sma_20')
        change_30d = tech.get('change_30d')
        
        # 30-day drop
        if change_30d is not None:
            if change_30d < -20:
                score += 30
                reasons.append(f"30-day drop: {change_30d:.1f}%")
            elif change_30d < -15:
                score += 25
                reasons.append(f"Significant 30-day decline: {change_30d:.1f}%")
            elif change_30d < -10:
                score += 20
                reasons.append(f"Moderate 30-day decline: {change_30d:.1f}%")
            elif change_30d < -5:
                score += 10
        
        # 52-week position
        if position_52w < 20:
            score += 30
            reasons.append(f"Near 52-week low ({position_52w:.0f}% of range)")
        elif position_52w < 30:
            score += 25
            reasons.append(f"Low in 52-week range ({position_52w:.0f}%)")
        elif position_52w < 40:
            score += 20
        
        # RSI oversold
        if rsi is not None:
            if rsi < 30:
                score += 20
                reasons.append(f"RSI oversold ({rsi:.1f})")
            elif rsi < 40:
                score += 15
                reasons.append(f"RSI approaching oversold ({rsi:.1f})")
            elif rsi < 50:
                score += 10
        
        # Below SMA
        if sma_20 and current_price:
            diff_pct = ((current_price - sma_20) / sma_20) * 100
            if current_price < sma_20 * 0.9:
                score += 20
                reasons.append(f"10%+ below SMA20 ({diff_pct:.1f}%)")
            elif current_price < sma_20 * 0.95:
                score += 15
                reasons.append(f"Below SMA20 ({diff_pct:.1f}%)")
            elif current_price < sma_20:
                score += 10
        
        return min(score, 100), reasons
    
    def _calculate_technical_strength(self, tech: Dict) -> tuple:
        """Calculate technical strength score (0-100) and reasons"""
        score = 0
        reasons = []
        
        current_price = tech.get('current_price', 0)
        sma_50 = tech.get('sma_50')
        rsi = tech.get('rsi')
        volatility = tech.get('volatility', 0)
        
        # Price stability (low volatility)
        if volatility < 2:
            score += 30
            reasons.append("Low price volatility")
        elif volatility < 3:
            score += 20
            reasons.append("Moderate volatility")
        elif volatility < 4:
            score += 10
        
        # RSI not extreme
        if rsi is not None:
            if 40 <= rsi <= 60:
                score += 30
                reasons.append("RSI in neutral zone")
            elif 30 <= rsi <= 70:
                score += 20
        
        # Near support (50-day MA)
        if sma_50 and current_price:
            diff_pct = abs(current_price - sma_50) / sma_50
            if diff_pct < 0.05:
                score += 40
                reasons.append("Price near 50-day support")
            elif diff_pct < 0.10:
                score += 20
        
        return min(score, 100), reasons
    
    def _get_label(self, score: float) -> str:
        """Get label for undervalued score"""
        if score >= 80:
            return "💎 Extremely Undervalued"
        elif score >= 70:
            return "💰 Highly Undervalued"
        elif score >= 60:
            return "📉 Undervalued"
        else:
            return "➡️ Watch"
