"""
Base Collector Module
Abstract base class for data collectors
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from src.utils.logger import get_logger

log = get_logger("collector")


class BaseCollector(ABC):
    """Abstract base class for data collectors"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize collector
        
        Args:
            config: Collector configuration
        """
        self.config = config or {}
        self._data: Dict[str, Any] = {}
    
    @abstractmethod
    def collect(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Collect data from source
        
        Returns:
            Collected data dictionary
        """
        pass
    
    def validate(self) -> bool:
        """
        Validate collector configuration
        
        Returns:
            True if valid, False otherwise
        """
        return True
    
    @property
    def data(self) -> Dict[str, Any]:
        """Get collected data"""
        return self._data
    
    def clear(self):
        """Clear collected data"""
        self._data = {}
    
    def _log_error(self, message: str, exception: Optional[Exception] = None):
        """Log error message"""
        if exception:
            log.error(f"{message}: {exception}")
        else:
            log.error(message)
    
    def _log_info(self, message: str):
        """Log info message"""
        log.info(message)
    
    def _log_warning(self, message: str):
        """Log warning message"""
        log.warning(message)
