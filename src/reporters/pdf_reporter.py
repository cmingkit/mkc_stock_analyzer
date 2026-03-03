"""
PDF Reporter Module
Generates PDF reports using WeasyPrint
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from src.reporters.base_reporter import BaseReporter
from src.reporters.html_reporter import HTMLReporter
from src.utils.logger import get_logger

log = get_logger("pdf_reporter")

# Try to import WeasyPrint
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    log.warning("WeasyPrint not installed, PDF generation unavailable")


class PDFReporter(BaseReporter):
    """Generates PDF reports"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize PDF reporter
        
        Args:
            config: Configuration dictionary with keys:
                - template_dir: Directory containing templates
                - output_dir: Directory for output files
        """
        super().__init__(config)
        
        # Set up paths
        project_root = Path(__file__).parent.parent.parent
        self.template_dir = Path(self.config.get('template_dir', project_root / 'templates'))
        self.output_dir = Path(self.config.get('output_dir', project_root / 'reports' / 'pdf'))
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # HTML reporter for generating content
        self.html_reporter = HTMLReporter(config)
    
    def generate(
        self, 
        data: Dict[str, Any], 
        output_path: Optional[str] = None,
        template_name: str = 'report.html'
    ) -> Optional[str]:
        """
        Generate PDF report
        
        Args:
            data: Data to include in report
            output_path: Path to save report (optional)
            template_name: Name of template file
        
        Returns:
            Path to generated report or None on error
        """
        if not WEASYPRINT_AVAILABLE:
            log.error("WeasyPrint not available, cannot generate PDF")
            return None
        
        log.info("Generating PDF report...")
        
        # Determine output path
        if output_path:
            self._output_path = Path(output_path)
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self._output_path = self.output_dir / f'report_{timestamp}.pdf'
        
        self._ensure_dir(self._output_path)
        
        try:
            # First generate HTML
            html_content = self.html_reporter.generate_summary(data)
            
            # Convert to PDF
            html_doc = HTML(string=html_content, base_url=str(self.template_dir))
            html_doc.write_pdf(str(self._output_path))
            
            log.info(f"PDF report generated: {self._output_path}")
            
            return str(self._output_path)
            
        except Exception as e:
            log.error(f"Failed to generate PDF report: {e}")
            return None
