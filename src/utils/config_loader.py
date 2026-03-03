"""
Configuration Loader Module
Handles loading YAML configuration and environment variables
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"


class ConfigLoader:
    """Configuration loader that handles YAML files and environment variables"""
    
    def __init__(self, settings_path: str = None, secrets_path: str = None):
        """
        Initialize configuration loader
        
        Args:
            settings_path: Path to settings.yaml
            secrets_path: Path to secrets.yaml
        """
        self.settings_path = Path(settings_path) if settings_path else CONFIG_DIR / "settings.yaml"
        self.secrets_path = Path(secrets_path) if secrets_path else CONFIG_DIR / "secrets.yaml"
        
        self._settings: Dict[str, Any] = {}
        self._secrets: Dict[str, Any] = {}
        
        # Load .env file if exists
        env_path = PROJECT_ROOT / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        
        self._load_settings()
        self._load_secrets()
    
    def _load_settings(self):
        """Load settings from YAML file"""
        if self.settings_path.exists():
            with open(self.settings_path, 'r', encoding='utf-8') as f:
                self._settings = yaml.safe_load(f) or {}
    
    def _load_secrets(self):
        """Load secrets from YAML file"""
        if self.secrets_path.exists():
            with open(self.secrets_path, 'r', encoding='utf-8') as f:
                self._secrets = yaml.safe_load(f) or {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key (supports dot notation)
        
        Args:
            key: Configuration key (e.g., 'collection.reddit.subreddits')
            default: Default value if key not found
        
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self._settings
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_secret(self, key: str, default: Any = None) -> Any:
        """
        Get secret value by key (supports dot notation)
        Also checks environment variables as fallback
        
        Args:
            key: Secret key (e.g., 'telegram.bot_token')
            default: Default value if key not found
        
        Returns:
            Secret value or default
        """
        # First check environment variable
        env_key = key.upper().replace('.', '_')
        env_value = os.getenv(env_key)
        if env_value:
            return env_value
        
        # Then check secrets file
        keys = key.split('.')
        value = self._secrets
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    @property
    def settings(self) -> Dict[str, Any]:
        """Get all settings"""
        return self._settings.copy()
    
    @property
    def secrets(self) -> Dict[str, Any]:
        """Get all secrets"""
        return self._secrets.copy()
    
    def get_telegram_config(self) -> Dict[str, str]:
        """Get Telegram configuration"""
        return {
            'bot_token': self.get_secret('telegram.bot_token'),
            'chat_id': self.get_secret('telegram.chat_id')
        }
    
    def get_reddit_config(self) -> Dict[str, str]:
        """Get Reddit configuration"""
        return {
            'client_id': self.get_secret('reddit.client_id'),
            'client_secret': self.get_secret('reddit.client_secret'),
            'user_agent': self.get_secret('reddit.user_agent', 'StockMonitorBot/1.0')
        }
    
    def get_alpha_vantage_config(self) -> Dict[str, str]:
        """Get Alpha Vantage configuration"""
        return {
            'api_key': self.get_secret('alpha_vantage.api_key')
        }


# Global config instance
_config: Optional[ConfigLoader] = None


def get_config() -> ConfigLoader:
    """Get global configuration instance"""
    global _config
    if _config is None:
        _config = ConfigLoader()
    return _config


def reload_config():
    """Reload configuration from files"""
    global _config
    _config = ConfigLoader()
    return _config
