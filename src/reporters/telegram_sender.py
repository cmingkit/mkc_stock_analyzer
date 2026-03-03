"""
Telegram Sender Module
Sends reports via Telegram Bot API
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

from src.reporters.base_reporter import BaseReporter
from src.utils.logger import get_logger
from src.utils.stock_info import get_stock_name

log = get_logger("telegram_sender")


class TelegramSender(BaseReporter):
    """Sends reports via Telegram"""
    
    MAX_MESSAGE_LENGTH = 4000
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Telegram sender
        
        Args:
            config: Configuration dictionary with keys:
                - bot_token: Telegram bot token
                - chat_id: Telegram chat ID
        """
        super().__init__(config)
        
        self.bot_token = self.config.get('bot_token')
        self.chat_id = self.config.get('chat_id')
    
    def generate(self, data: Dict[str, Any], *args, **kwargs) -> bool:
        """
        Generate and send Telegram message
        
        Args:
            data: Data to send
        
        Returns:
            True if successful, False otherwise
        """
        message = self.format_message(data)
        return self.send(message)
    
    def send(self, message: str) -> bool:
        """
        Send message to Telegram
        
        Args:
            message: Message to send
        
        Returns:
            True if successful, False otherwise
        """
        if not self.bot_token or not self.chat_id:
            log.warning("Telegram credentials not configured")
            return False
        
        # Truncate if too long
        if len(message) > self.MAX_MESSAGE_LENGTH:
            message = message[:self.MAX_MESSAGE_LENGTH] + "\n\n... (truncated)"
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if result.get('ok'):
                log.info(f"Telegram message sent successfully")
                return True
            else:
                log.error(f"Telegram API error: {result}")
                return False
                
        except Exception as e:
            log.error(f"Failed to send Telegram message: {e}")
            return False
    
    def format_message(self, data: Dict[str, Any]) -> str:
        """
        Format data as Telegram message
        
        Args:
            data: Analysis data
        
        Returns:
            Formatted message string
        """
        lines = []
        
        # Header
        lines.append("<b>📊 Stock Analyzer Report</b>")
        lines.append(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # Top stocks from sentiment analysis
        sentiment = data.get('sentiment_analysis', {})
        top_stocks = sentiment.get('top_stocks', [])
        
        if top_stocks:
            lines.append("<b>🔥 Hot Stocks (Reddit)</b>")
            
            for i, stock in enumerate(top_stocks[:10], 1):
                ticker = stock['ticker']
                name = stock.get('name', ticker)
                count = stock['count']
                sentiment_emoji = stock.get('sentiment_emoji', '➡️')
                bull_ratio = stock.get('bull_ratio', 0.5)
                risk = stock.get('risk_level', 'Unknown')
                
                lines.append(f"{i}. {sentiment_emoji} <b>{ticker}</b> ({name})")
                lines.append(f"    {count} mentions | {bull_ratio:.0%} bullish | Risk: {risk}")
            
            lines.append("")
        
        # Undervalued stocks
        risk = data.get('risk_analysis', {})
        undervalued = risk.get('undervalued_stocks', [])
        
        if undervalued:
            lines.append("<b>💎 Undervalued Stocks</b>")
            
            for i, stock in enumerate(undervalued[:5], 1):
                ticker = stock['ticker']
                name = stock.get('name', ticker)
                score = stock['score']
                label = stock.get('label', 'Watch')
                price = stock.get('current_price')
                rsi = stock.get('rsi')
                
                lines.append(f"{i}. {label} <b>{ticker}</b> ({name})")
                
                if price and rsi:
                    lines.append(f"    Score: {score:.0f} | ${price:.2f} | RSI: {rsi:.1f}")
                else:
                    lines.append(f"    Score: {score:.0f}")
            
            lines.append("")
        
        # Event alerts
        alerts = data.get('event_alerts', [])
        if alerts:
            lines.append("<b>📅 Event Alerts</b>")
            for alert in alerts:
                lines.append(f"• {alert}")
            lines.append("")
        
        # Disclaimer
        lines.append("<i>⚠️ For informational purposes only. Not investment advice.</i>")
        
        return "\n".join(lines)
    
    def send_alert(self, title: str, message: str) -> bool:
        """
        Send alert message
        
        Args:
            title: Alert title
            message: Alert message
        
        Returns:
            True if successful
        """
        full_message = f"🚨 <b>{title}</b>\n\n{message}"
        return self.send(full_message)
