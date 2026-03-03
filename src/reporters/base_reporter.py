"""
Base Reporter Module
Abstract base class for reporters
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional

from src.utils.logger import get_logger

log = get_logger("reporter")


class BaseReporter(ABC):
    """Abstract base class for reporters"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize reporter
        
        Args:
            config: Reporter configuration
        """
        self.config = config or {}
        self._output_path: Optional[Path] = None
    
    @abstractmethod
    def generate(self, data: Dict[str, Any], output_path: Optional[str] = None) -> str:
        """
        Generate report
        
        Args:
            data: Data to report
            output_path: Path to save report (optional)
        
        Returns:
            Path to generated report or report content
        """
        pass
    
    @property
    def output_path(self) -> Optional[Path]:
        """Get output path"""
        return self._output_path
    
    def _ensure_dir(self, path: Path):
        """Ensure directory exists"""
        path.parent.mkdir(parents=True, exist_ok=True)
    
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
