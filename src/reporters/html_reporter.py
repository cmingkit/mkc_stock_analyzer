"""
HTML Reporter Module - GitHub Pages Compatible Version
Generates HTML reports using Jinja2 templates
Updated for v2.0 redesign with Executive Summary and Composite Scores
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.reporters.base_reporter import BaseReporter
from src.utils.logger import get_logger

log = get_logger("html_reporter")


class HTMLReporter(BaseReporter):
    """Generates HTML reports with enhanced visualizations"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        project_root = Path(__file__).parent.parent.parent
        self.template_dir = Path(self.config.get('template_dir', project_root / 'templates'))
        self.output_dir = Path(self.config.get('output_dir', project_root / 'reports' / 'html'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # GitHub Pages mode - adjust static file paths
        self.for_github_pages = self.config.get('for_github_pages', False)
        
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )
    
    def generate(self, data: Dict[str, Any], output_path: Optional[str] = None, template_name: str = 'report.html') -> str:
        log.info("Generating HTML report...")
        if output_path:
            self._output_path = Path(output_path)
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self._output_path = self.output_dir / f'report_{timestamp}.html'
        self._ensure_dir(self._output_path)
        context = self._prepare_context(data)
        try:
            template = self.env.get_template(template_name)
            html_content = template.render(**context)
            with open(self._output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            log.info(f"HTML report generated: {self._output_path}")
            return str(self._output_path)
        except Exception as e:
            log.error(f"Failed to generate HTML report: {e}")
            raise
    
    def _prepare_context(self, data: Dict[str, Any]) -> Dict[str, Any]:
        sentiment_data = data.get('sentiment_analysis', {})
        technical_data = data.get('technical_analysis', {}).get('analysis', {})
        risk_data = data.get('risk_analysis', {})
        price_data = data.get('price_data', {}).get('price_data', {})
        
        top_stocks = self._enhance_stocks(sentiment_data.get('top_stocks', []), technical_data, price_data)
        undervalued_stocks = self._enhance_undervalued(risk_data.get('undervalued_stocks', []), technical_data, price_data)
        chart_data = self._prepare_chart_data(top_stocks, undervalued_stocks, price_data, technical_data)
        
        total_mentions = sentiment_data.get('total_mentions', 0)
        avg_sentiment = self._calculate_avg_sentiment(top_stocks)
        
        # Executive Summary Data
        market_summary = self._calculate_market_summary(top_stocks)
        key_risks = self._extract_key_risks(risk_data, top_stocks)
        event_alerts = self._prepare_event_alerts(data.get('event_alerts', []), top_stocks, technical_data)
        
        # Determine static file paths based on GitHub Pages mode
        if self.for_github_pages:
            # For GitHub Pages: reports are in docs/reports/, static in docs/static/
            css_path = "../static/css/report.css"
            js_path = "../static/js/chart.min.js"
        else:
            # For local: reports in reports/html/, static in static/
            css_path = "../../static/css/report.css"
            js_path = "../../static/js/chart.min.js"
        
        return {
            'title': 'Stock Analysis Report',
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data_period': '7 days',
            'total_mentions': total_mentions,
            'avg_sentiment': avg_sentiment,
            'stocks_analyzed': len(top_stocks),
            'market_trend': market_summary['market_trend'],
            'market_trend_emoji': market_summary['market_trend_emoji'],
            'market_bull_ratio': market_summary['market_bull_ratio'],
            'bullish_count': market_summary['bullish_count'],
            'bearish_count': market_summary['bearish_count'],
            'neutral_count': market_summary['neutral_count'],
            'key_risks': key_risks,
            'event_alerts': event_alerts,
            'top_stocks': top_stocks,
            'undervalued_stocks': undervalued_stocks,
            'reddit_stats': {'total_posts': total_mentions, 'period': '7 days'},
            'price_update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'chart_data_json': json.dumps(chart_data),
            # Add path variables for template
            'css_path': css_path,
            'js_path': js_path
        }
    
    def _calculate_composite_score(self, stock: Dict) -> int:
        sentiment_score = stock.get('bull_ratio', 0.5) * 100
        tech = stock.get('technical', {})
        rsi = tech.get('rsi', 50) if tech else 50
        if rsi < 30:
            technical_score = 80
        elif rsi > 70:
            technical_score = 40
        else:
            technical_score = 70
        trend = tech.get('trend', 'neutral') if tech else 'neutral'
        if trend in ['strong_up', 'up']:
            technical_score = min(100, technical_score + 10)
        elif trend in ['strong_down', 'down']:
            technical_score = max(0, technical_score - 10)
        fundamentals = stock.get('fundamentals', {})
        if fundamentals and fundamentals.get('pe_ratio'):
            pe = fundamentals.get('pe_ratio', 0)
            industry_pe = fundamentals.get('industry_pe', pe)
            if pe > 0 and industry_pe > 0:
                pe_ratio = pe / industry_pe
                if pe_ratio < 0.8: fundamental_score = 85
                elif pe_ratio < 1.0: fundamental_score = 70
                elif pe_ratio < 1.2: fundamental_score = 55
                else: fundamental_score = 40
            else: fundamental_score = 60
        else: fundamental_score = 65
        risk_level = stock.get('risk_level', 'Medium')
        risk_scores = {'Low': 90, 'Medium': 60, 'High': 30, 'Unknown': 60}
        risk_score = risk_scores.get(risk_level, 60)
        composite = sentiment_score * 0.4 + technical_score * 0.3 + fundamental_score * 0.2 + risk_score * 0.1
        return round(min(100, max(0, composite)))
    
    def _determine_action(self, score: int, stock: Dict) -> Tuple[str, str]:
        tech = stock.get('technical', {})
        rsi = tech.get('rsi', 50) if tech else 50
        sentiment = stock.get('sentiment', 'neutral')
        if score >= 75 and rsi < 70 and sentiment == 'positive':
            return 'BUY', '🟢'
        elif score <= 40 or rsi > 70 or sentiment == 'negative':
            return 'SELL', '🔴'
        else:
            return 'HOLD', '🟡'
    
    def _calculate_score_components(self, stock: Dict) -> List[Dict]:
        components = []
        sentiment_score = round(stock.get('bull_ratio', 0.5) * 100)
        components.append({'name': '情緒分析', 'score': sentiment_score, 'class': 'sentiment'})
        tech = stock.get('technical', {})
        rsi = tech.get('rsi', 50) if tech else 50
        if rsi < 30: technical_score = 80
        elif rsi > 70: technical_score = 40
        else: technical_score = 70
        components.append({'name': '技術面', 'score': technical_score, 'class': 'technical'})
        fundamentals = stock.get('fundamentals', {})
        if fundamentals and fundamentals.get('pe_ratio'):
            pe = fundamentals.get('pe_ratio', 0)
            industry_pe = fundamentals.get('industry_pe', pe)
            if pe > 0 and industry_pe > 0:
                pe_ratio = pe / industry_pe
                if pe_ratio < 0.8: fundamental_score = 85
                elif pe_ratio < 1.0: fundamental_score = 70
                elif pe_ratio < 1.2: fundamental_score = 55
                else: fundamental_score = 40
            else: fundamental_score = 60
        else: fundamental_score = 65
        components.append({'name': '基本面', 'score': fundamental_score, 'class': 'fundamental'})
        risk_level = stock.get('risk_level', 'Medium')
        risk_scores = {'Low': 90, 'Medium': 60, 'High': 30, 'Unknown': 60}
        components.append({'name': '風險評估', 'score': risk_scores.get(risk_level, 60), 'class': 'risk'})
        return components
    
    def _calculate_market_summary(self, stocks: List[Dict]) -> Dict:
        if not stocks:
            return {'market_trend': 'neutral', 'market_trend_emoji': '➡️', 'market_bull_ratio': 50, 'bullish_count': 0, 'bearish_count': 0, 'neutral_count': 0}
        bullish = sum(1 for s in stocks if s.get('sentiment') == 'positive')
        bearish = sum(1 for s in stocks if s.get('sentiment') == 'negative')
        neutral = len(stocks) - bullish - bearish
        avg_bull_ratio = sum(s.get('bull_ratio', 0.5) for s in stocks) / len(stocks) * 100
        if avg_bull_ratio >= 60:
            return {'market_trend': 'bullish', 'market_trend_emoji': '📈', 'market_bull_ratio': round(avg_bull_ratio), 'bullish_count': bullish, 'bearish_count': bearish, 'neutral_count': neutral}
        elif avg_bull_ratio <= 40:
            return {'market_trend': 'bearish', 'market_trend_emoji': '📉', 'market_bull_ratio': round(avg_bull_ratio), 'bullish_count': bullish, 'bearish_count': bearish, 'neutral_count': neutral}
        else:
            return {'market_trend': 'neutral', 'market_trend_emoji': '➡️', 'market_bull_ratio': round(avg_bull_ratio), 'bullish_count': bullish, 'bearish_count': bearish, 'neutral_count': neutral}
    
    def _extract_key_risks(self, risk_data: Dict, stocks: List[Dict]) -> List[Dict]:
        risks = []
        high_risk_count = sum(1 for s in stocks if s.get('risk_level') == 'High')
        if high_risk_count > 3:
            risks.append({'level': 'high', 'icon': '🔴', 'text': f'{high_risk_count} 檔高風險股票'})
        overbought_count = sum(1 for s in stocks if s.get('technical', {}).get('rsi', 50) > 70)
        if overbought_count > 2:
            risks.append({'level': 'medium', 'icon': '🟡', 'text': f'{overbought_count} 檔股票超買'})
        bearish_count = sum(1 for s in stocks if s.get('sentiment') == 'negative')
        if bearish_count > len(stocks) * 0.3:
            risks.append({'level': 'medium', 'icon': '🟡', 'text': '市場情緒偏空'})
        if not risks:
            risks.append({'level': 'low', 'icon': '✅', 'text': '目前無重大風險'})
        return risks[:5]
    
    def _prepare_event_alerts(self, alerts: List, stocks: List[Dict], technical_data: Dict) -> List[Dict]:
        prepared = []
        for alert in alerts[:3]:
            if isinstance(alert, dict):
                prepared.append({'severity': alert.get('severity', 'medium'), 'icon': alert.get('icon', '📌'), 'title': alert.get('title', str(alert)), 'time': alert.get('time', '')})
            else:
                prepared.append({'severity': 'medium', 'icon': '📌', 'title': str(alert), 'time': ''})
        for stock in stocks[:5]:
            tech = stock.get('technical', {})
            change_7d = tech.get('change_7d', 0) if tech else 0
            if abs(change_7d) > 10:
                prepared.append({'severity': 'high' if abs(change_7d) > 15 else 'medium', 'icon': '📈' if change_7d > 0 else '📉', 'title': f"{stock['ticker']} 7日{'上漲' if change_7d > 0 else '下跌'} {abs(change_7d):.1f}%", 'time': '最近7天'})
        return prepared[:5]
    
    def _calculate_support_resistance(self, stock: Dict, price_data: Dict) -> Tuple[List[str], List[str]]:
        current_price = stock.get('current_price', 0)
        if not current_price or current_price <= 0:
            return ['N/A'], ['N/A']
        support = [f"${current_price * 0.95:.2f}", f"${current_price * 0.90:.2f}"]
        resistance = [f"${current_price * 1.05:.2f}", f"${current_price * 1.10:.2f}"]
        return support, resistance
    
    def _enhance_stocks(self, stocks: List[Dict], technical_data: Dict, price_data: Dict) -> List[Dict]:
        enhanced = []
        for stock in stocks:
            ticker = stock.get('ticker', '')
            tech = technical_data.get(ticker, {})
            stock['technical'] = tech
            if not stock.get('current_price'):
                if tech and tech.get('current_price'):
                    stock['current_price'] = tech.get('current_price')
                elif ticker in price_data:
                    history = price_data.get(ticker, {}).get('history', [])
                    if history:
                        stock['current_price'] = history[-1][1]
            if tech:
                stock['technical']['signal_type'], stock['technical']['signal_text'], stock['technical']['signal_emoji'] = self._interpret_technical_signal(tech)
            stock['score'] = self._calculate_composite_score(stock)
            stock['action'], stock['action_emoji'] = self._determine_action(stock['score'], stock)
            stock['score_components'] = self._calculate_score_components(stock)
            support, resistance = self._calculate_support_resistance(stock, price_data.get(ticker, {}))
            stock['support_levels'] = support
            stock['resistance_levels'] = resistance
            current_price = stock.get('current_price', 0)
            if current_price and current_price > 0:
                stock['entry_price'] = round(current_price * 0.98, 2)
                stock['target_price'] = round(current_price * 1.10, 2)
                stock['stop_loss'] = round(current_price * 0.92, 2)
            else:
                stock['entry_price'] = None
                stock['target_price'] = None
                stock['stop_loss'] = None
            stock['rationale'] = self._generate_rationale(stock)
            stock['fundamentals'] = self._get_fundamentals(ticker, price_data.get(ticker, {}))
            stock['valuation_factors'] = self._calculate_valuation_factors(stock)
            stock['valuation_label'] = self._get_valuation_label(stock.get('bull_ratio', 0.5))
            stock['risk_factors'] = self._get_risk_factors(stock, tech)
            stock['risk_position'] = self._calculate_risk_position(stock.get('risk_level', 'Medium'))
            stock['advice'] = self._generate_advice(stock, tech)
            total = stock.get('positive', 0) + stock.get('negative', 0) + stock.get('neutral', 0)
            if total >= 20: stock['confidence'] = 'High'
            elif total >= 10: stock['confidence'] = 'Medium'
            else: stock['confidence'] = 'Low'
            stock['analysis_period'] = '7 days'
            stock['keywords'] = self._extract_keywords(stock.get('posts', []))
            stock['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M')
            if ticker in price_data and price_data[ticker].get('history'):
                stock['price_chart'] = True
            enhanced.append(stock)
        return enhanced
    
    def _generate_rationale(self, stock: Dict) -> str:
        parts = []
        bull_ratio = stock.get('bull_ratio', 0.5)
        if bull_ratio > 0.6: parts.append('強烈看漲情緒')
        elif bull_ratio > 0.5: parts.append('偏多情緒')
        elif bull_ratio < 0.4: parts.append('偏空情緒')
        tech = stock.get('technical', {})
        rsi = tech.get('rsi', 50) if tech else 50
        if rsi < 30: parts.append('超賣區')
        elif rsi > 70: parts.append('超買區')
        risk = stock.get('risk_level', 'Medium')
        if risk == 'Low': parts.append('低風險')
        elif risk == 'High': parts.append('高風險')
        return '，'.join(parts) if parts else '基於技術面和基本面綜合分析'
    
    def _enhance_undervalued(self, stocks: List[Dict], technical_data: Dict, price_data: Dict) -> List[Dict]:
        enhanced = []
        for stock in stocks:
            reasons = []
            if stock.get('oversold_score', 0) >= 50: reasons.append("Oversold conditions detected")
            if stock.get('neglect_score', 0) >= 50: reasons.append("Under-discussed on social media")
            if stock.get('technical_score', 0) >= 50: reasons.append("Favorable technical indicators")
            if stock.get('rsi') and stock['rsi'] < 40: reasons.append(f"Low RSI ({stock['rsi']:.1f})")
            stock['reasons'] = reasons
            enhanced.append(stock)
        return enhanced
    
    def _prepare_chart_data(self, top_stocks: List[Dict], undervalued_stocks: List[Dict], price_data: Dict, technical_data: Dict) -> Dict[str, Any]:
        chart_data = {'sentiment': {}, 'sentimentTrend': {}, 'price': {}, 'comparison': {}}
        for stock in top_stocks[:10]:
            ticker = stock.get('ticker', '')
            chart_data['sentiment'][ticker] = {'positive': stock.get('positive', 0), 'neutral': stock.get('neutral', 0), 'negative': stock.get('negative', 0)}
            if ticker in price_data:
                history = price_data[ticker].get('history', [])
                if history:
                    prices = [h[1] for h in history[-30:]]
                    dates = [h[0].strftime('%m/%d') for h in history[-30:]]
                    chart_data['price'][ticker] = {'dates': dates, 'prices': prices, 'sma20': self._calculate_sma_list(prices, 20), 'sma50': self._calculate_sma_list(prices, 50), 'ema12': self._calculate_ema_list(prices, 12), 'volumes': []}
        for stock in undervalued_stocks[:5]:
            ticker = stock.get('ticker', '')
            chart_data['comparison'][ticker] = {'stock': [min(100, stock.get('oversold_score', 50)), min(100, stock.get('neglect_score', 50)), min(100, stock.get('technical_score', 50)), 50, 50, 50], 'industry': [50, 50, 50, 50, 50, 50]}
        return chart_data
    
    def _interpret_technical_signal(self, tech: Dict) -> tuple:
        rsi = tech.get('rsi')
        trend = tech.get('trend', 'neutral')
        buy_signals = 0
        sell_signals = 0
        if rsi:
            if rsi < 30: buy_signals += 2
            elif rsi < 40: buy_signals += 1
            elif rsi > 70: sell_signals += 2
            elif rsi > 60: sell_signals += 1
        if trend in ['strong_up', 'up']: buy_signals += 1
        elif trend in ['strong_down', 'down']: sell_signals += 1
        if buy_signals >= 2: return 'buy', 'BUY', '🟢'
        elif sell_signals >= 2: return 'sell', 'SELL', '🔴'
        else: return 'hold', 'HOLD', '🟡'
    
    def _get_fundamentals(self, ticker: str, price_info: Dict) -> Dict:
        """Get fundamental data using yfinance"""
        fundamentals = {
            'pe_ratio': None, 'pb_ratio': None, 'roe': None, 'debt_equity': None,
            'industry_pe': None, 'industry_pb': None, 'industry_roe': None, 'industry_de': None,
            'pe_status': 'neutral', 'pb_status': 'neutral', 'roe_status': 'neutral', 'de_status': 'neutral',
            'pe_status_emoji': '➡️', 'pb_status_emoji': '➡️', 'roe_status_emoji': '➡️', 'de_status_emoji': '➡️'
        }
        
        try:
            import yfinance as yf
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # P/E Ratio (本益比)
            pe = info.get('trailingPE') or info.get('forwardPE')
            if pe is not None:
                fundamentals['pe_ratio'] = round(pe, 2) if isinstance(pe, (int, float)) else pe
            
            # P/B Ratio (股價淨值比)
            pb = info.get('priceToBook')
            if pb is not None:
                fundamentals['pb_ratio'] = round(pb, 2) if isinstance(pb, (int, float)) else pb
            
            # ROE (股東權益報酬率) - yfinance 返回小數形式
            roe = info.get('returnOnEquity')
            if roe is not None and isinstance(roe, (int, float)):
                # yfinance ROE 是小數形式，轉換為百分比
                fundamentals['roe'] = round(roe * 100, 2)
            
            # Debt/Equity (負債比率)
            de = info.get('debtToEquity')
            if de is not None:
                fundamentals['debt_equity'] = round(de, 2) if isinstance(de, (int, float)) else de
            
            # Industry benchmarks (使用合理估計值)
            industry_pe = 25.0  # 科技股平均 P/E
            industry_pb = 5.0   # 平均 P/B
            industry_roe = 15.0 # 平均 ROE 15%
            industry_de = 50.0  # 平均 D/E 50%
            
            fundamentals['industry_pe'] = industry_pe
            fundamentals['industry_pb'] = industry_pb
            fundamentals['industry_roe'] = industry_roe
            fundamentals['industry_de'] = industry_de
            
            # Calculate status
            if fundamentals['pe_ratio'] is not None:
                pe_ratio = fundamentals['pe_ratio'] / industry_pe if industry_pe > 0 else 1
                if pe_ratio < 0.8:
                    fundamentals['pe_status'] = 'good'
                    fundamentals['pe_status_emoji'] = '🟢'
                elif pe_ratio > 1.2:
                    fundamentals['pe_status'] = 'poor'
                    fundamentals['pe_status_emoji'] = '🔴'
            
            if fundamentals['pb_ratio'] is not None:
                pb_ratio = fundamentals['pb_ratio'] / industry_pb if industry_pb > 0 else 1
                if pb_ratio < 0.8:
                    fundamentals['pb_status'] = 'good'
                    fundamentals['pb_status_emoji'] = '🟢'
                elif pb_ratio > 1.2:
                    fundamentals['pb_status'] = 'poor'
                    fundamentals['pb_status_emoji'] = '🔴'
            
            if fundamentals['roe'] is not None:
                if fundamentals['roe'] > 20:
                    fundamentals['roe_status'] = 'good'
                    fundamentals['roe_status_emoji'] = '🟢'
                elif fundamentals['roe'] < 10:
                    fundamentals['roe_status'] = 'poor'
                    fundamentals['roe_status_emoji'] = '🔴'
            
            if fundamentals['debt_equity'] is not None:
                if fundamentals['debt_equity'] < 30:
                    fundamentals['de_status'] = 'good'
                    fundamentals['de_status_emoji'] = '🟢'
                elif fundamentals['debt_equity'] > 70:
                    fundamentals['de_status'] = 'poor'
                    fundamentals['de_status_emoji'] = '🔴'
            
            log.info(f"Fundamentals for {ticker}: P/E={fundamentals['pe_ratio']}, P/B={fundamentals['pb_ratio']}, ROE={fundamentals['roe']}%, D/E={fundamentals['debt_equity']}")
            
        except Exception as e:
            log.warning(f"Failed to get fundamentals for {ticker}: {e}")
        
        return fundamentals
    
    def _calculate_valuation_factors(self, stock: Dict) -> List[Dict]:
        factors = []
        bull_ratio = stock.get('bull_ratio', 0.5)
        factors.append({'name': 'Sentiment', 'score': round(bull_ratio * 10, 1)})
        risk_level = stock.get('risk_level', 'Medium')
        risk_score = {'Low': 8, 'Medium': 5, 'High': 3, 'Unknown': 5}.get(risk_level, 5)
        factors.append({'name': 'Risk Level', 'score': risk_score})
        tech = stock.get('technical', {})
        if tech:
            rsi = tech.get('rsi', 50)
            if rsi < 30: tech_score = 8
            elif rsi > 70: tech_score = 3
            else: tech_score = 6
            factors.append({'name': 'Technical', 'score': tech_score})
        return factors
    
    def _get_valuation_label(self, bull_ratio: float) -> str:
        if bull_ratio >= 0.7: return 'Overvalued'
        elif bull_ratio >= 0.55: return 'Fairly Valued'
        elif bull_ratio >= 0.4: return 'Slightly Undervalued'
        else: return 'Undervalued'
    
    def _get_risk_factors(self, stock: Dict, tech: Dict) -> List[Dict]:
        factors = []
        if stock.get('bull_ratio', 0) > 0.6: factors.append({'type': 'positive', 'icon': '✅', 'text': '強烈看漲情緒'})
        if tech and tech.get('rsi') and 40 <= tech.get('rsi') <= 60: factors.append({'type': 'positive', 'icon': '✅', 'text': 'RSI 在正常區間'})
        if stock.get('bull_ratio', 0) < 0.4: factors.append({'type': 'negative', 'icon': '⚠️', 'text': '偏空情緒'})
        if tech and tech.get('rsi') and tech.get('rsi') > 70: factors.append({'type': 'negative', 'icon': '⚠️', 'text': '超買狀態'})
        if not factors: factors.append({'type': 'neutral', 'icon': '➡️', 'text': '信號混合'})
        return factors[:4]
    
    def _calculate_risk_position(self, risk_level: str) -> int:
        return {'Low': 20, 'Medium': 50, 'High': 80, 'Unknown': 50}.get(risk_level, 50)
    
    def _generate_advice(self, stock: Dict, tech: Dict) -> Dict:
        current_price = stock.get('current_price')
        if not current_price and tech: current_price = tech.get('current_price')
        if not current_price or current_price <= 0:
            return {'action': 'HOLD', 'entry_price': None, 'exit_price': None, 'stop_loss': None, 'take_profit': None, 'risk_notice': 'Insufficient price data for advice', 'data_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        price_warning = None
        if current_price > 10000 or current_price < 0.01: price_warning = f'Warning: Unusual price detected (${current_price:.2f}). Verify data.'
        rsi = tech.get('rsi', 50) if tech else 50
        if rsi < 30:
            risk_notice = 'RSI indicates oversold condition. Verify with volume before entry.'
            if price_warning: risk_notice = f'{price_warning} {risk_notice}'
            return {'action': 'BUY', 'entry_price': round(current_price * 0.98, 2), 'exit_price': round(current_price * 1.15, 2), 'stop_loss': round(current_price * 0.92, 2), 'take_profit': round(current_price * 1.10, 2), 'risk_notice': risk_notice, 'data_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'current_price': round(current_price, 2)}
        elif rsi > 70:
            risk_notice = 'RSI indicates overbought condition. Consider taking profits.'
            if price_warning: risk_notice = f'{price_warning} {risk_notice}'
            return {'action': 'SELL', 'entry_price': None, 'exit_price': round(current_price, 2), 'stop_loss': None, 'take_profit': None, 'risk_notice': risk_notice, 'data_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'current_price': round(current_price, 2)}
        else:
            risk_notice = 'Neutral conditions. Wait for clearer signals.'
            if price_warning: risk_notice = f'{price_warning} {risk_notice}'
            return {'action': 'HOLD', 'entry_price': round(current_price * 0.95, 2), 'exit_price': round(current_price * 1.10, 2), 'stop_loss': round(current_price * 0.90, 2), 'take_profit': round(current_price * 1.08, 2), 'risk_notice': risk_notice, 'data_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'current_price': round(current_price, 2)}
    
    def _extract_keywords(self, posts: List[Dict]) -> List[Dict]:
        word_count = {}
        for post in posts[:20]:
            title = post.get('title', '')
            for word in title.split():
                word = word.lower().strip('.,!?;:')
                if len(word) >= 3 and word.isalpha():
                    word_count[word] = word_count.get(word, 0) + 1
        sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)[:10]
        if not sorted_words: return []
        max_count = sorted_words[0][1]
        return [{'word': w, 'size': round(0.8 + (c / max_count) * 0.7, 2)} for w, c in sorted_words]
    
    def _calculate_avg_sentiment(self, stocks: List[Dict]) -> str:
        if not stocks: return 'Neutral'
        avg_bull = sum(s.get('bull_ratio', 0.5) for s in stocks) / len(stocks)
        if avg_bull >= 0.6: return 'Bullish'
        elif avg_bull <= 0.4: return 'Bearish'
        else: return 'Neutral'
    
    def _calculate_sma_list(self, prices: List[float], period: int) -> List[Optional[float]]:
        sma = []
        for i in range(len(prices)):
            if i < period - 1: sma.append(None)
            else: sma.append(sum(prices[i-period+1:i+1]) / period)
        return sma
    
    def _calculate_ema_list(self, prices: List[float], period: int) -> List[Optional[float]]:
        if len(prices) < period: return [None] * len(prices)
        ema = [None] * (period - 1)
        multiplier = 2 / (period + 1)
        ema.append(sum(prices[:period]) / period)
        for i in range(period, len(prices)):
            ema.append((prices[i] - ema[-1]) * multiplier + ema[-1])
        return ema
    
    def generate_summary(self, data: Dict[str, Any]) -> str:
        context = {'title': 'Stock Analysis Summary', 'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'top_stocks': data.get('sentiment_analysis', {}).get('top_stocks', [])[:5], 'undervalued_stocks': data.get('risk_analysis', {}).get('undervalued_stocks', [])[:3]}
        try:
            template = self.env.get_template('summary.html')
            return template.render(**context)
        except Exception:
            return self._generate_simple_html(context)
    
    def _generate_simple_html(self, context: Dict) -> str:
        html = [f'<!DOCTYPE html><html><head><title>{context["title"]}</title><style>body{{font-family:Arial,sans-serif;margin:20px;}}h1{{color:#333;}}.stock{{margin:10px 0;padding:10px;border:1px solid #ddd;}}.positive{{color:green;}}.negative{{color:red;}}.neutral{{color:gray;}}</style></head><body><h1>{context["title"]}</h1><p>Generated:{context["generated_at"]}</p>']
        if context['top_stocks']:
            html.append('<h2>Top Stocks</h2>')
            for stock in context['top_stocks']:
                html.append(f'<div class="stock"><strong>{stock["ticker"]}</strong>({stock.get("name","")})<br>Mentions:{stock["count"]}|Sentiment:<span class="{stock["sentiment"]}">{stock["sentiment"]}</span></div>')
        html.append('</body></html>')
        return '\n'.join(html)
