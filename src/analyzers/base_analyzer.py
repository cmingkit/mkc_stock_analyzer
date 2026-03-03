"""
Base Analyzer Module
Abstract base class for analyzers
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from src.utils.logger import get_logger

log = get_logger("analyzer")


class BaseAnalyzer(ABC):
    """Abstract base class for analyzers"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize analyzer
        
        Args:
            config: Analyzer configuration
        """
        self.config = config or {}
        self._results: Dict[str, Any] = {}
    
    @abstractmethod
    def analyze(self, data: Dict[str, Any], *args, **kwargs) -> Dict[str, Any]:
        """
        Analyze data
        
        Args:
            data: Data to analyze
        
        Returns:
            Analysis results
        """
        pass
    
    @property
    def results(self) -> Dict[str, Any]:
        """Get analysis results"""
        return self._results
    
    def clear(self):
        """Clear analysis results"""
        self._results = {}
    
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
