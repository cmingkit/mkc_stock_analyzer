#!/usr/bin/env python3
"""
Publisher Module - Publish HTML reports via various methods
"""

import json
import os
import subprocess
import sys
import tempfile
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class ReportPublisher:
    """Handle publishing of HTML reports"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.reports_dir = project_root / 'reports' / 'html'
        self.scripts_dir = project_root / 'scripts'
    
    def get_latest_report(self) -> Optional[Path]:
        """Get the path to the latest HTML report"""
        if not self.reports_dir.exists():
            return None
        
        reports = list(self.reports_dir.glob('*.html'))
        if not reports:
            return None
        
        # Sort by modification time, get newest
        return max(reports, key=lambda p: p.stat().st_mtime)
    
    def get_all_reports(self) -> List[Path]:
        """Get all HTML reports sorted by modification time (newest first)"""
        if not self.reports_dir.exists():
            return []
        
        reports = list(self.reports_dir.glob('*.html'))
        return sorted(reports, key=lambda p: p.stat().st_mtime, reverse=True)
    
    def serve_local(self, port: int = 8080, open_browser: bool = True) -> Tuple[bool, str]:
        """
        Start a local HTTP server for reports
        
        Args:
            port: Port number to use
            open_browser: Whether to open browser automatically
            
        Returns:
            Tuple of (success, message)
        """
        latest = self.get_latest_report()
        if not latest:
            return False, "No HTML reports found. Run the analyzer first."
        
        url = f"http://localhost:{port}"
        
        if open_browser:
            # Open in browser after a short delay
            import threading
            import time
            
            def open_url():
                time.sleep(1)
                webbrowser.open(url)
            
            threading.Thread(target=open_url, daemon=True).start()
        
        print(f"\n{'='*50}")
        print(f"   Stock Analyzer - Local Report Server")
        print(f"{'='*50}")
        print(f"\n  Serving reports at: {url}")
        if latest:
            print(f"  Latest report: {url}/{latest.name}")
        print(f"\n  Press Ctrl+C to stop\n")
        
        # Start server
        os.chdir(self.reports_dir)
        subprocess.run([sys.executable, '-m', 'http.server', str(port)])
        
        return True, url
    
    def publish_ngrok(self, port: int = 8080) -> Tuple[bool, str]:
        """
        Publish reports via ngrok for public access
        
        Args:
            port: Local port to tunnel
            
        Returns:
            Tuple of (success, public_url or error_message)
        """
        # Check ngrok installation
        try:
            result = subprocess.run(['ngrok', 'version'], capture_output=True, text=True)
        except FileNotFoundError:
            return False, "ngrok is not installed. Install from https://ngrok.com"
        
        # Run the public_reports.sh script
        script_path = self.scripts_dir / 'public_reports.sh'
        if not script_path.exists():
            return False, f"Script not found: {script_path}"
        
        # Execute script
        os.system(f'bash "{script_path}" {port}')
        
        return True, "ngrok server started"
    
    def publish_github(
        self,
        repo_url: Optional[str] = None,
        branch: str = 'gh-pages',
        latest_only: bool = False,
        dry_run: bool = False
    ) -> Tuple[bool, str]:
        """
        Publish reports to GitHub Pages
        
        Args:
            repo_url: GitHub repository URL (required for first run)
            branch: Branch to publish to
            latest_only: Only publish the latest report
            dry_run: Show what would be done without making changes
            
        Returns:
            Tuple of (success, message)
        """
        script_path = self.scripts_dir / 'publish_to_github.sh'
        if not script_path.exists():
            return False, f"Script not found: {script_path}"
        
        # Build command
        cmd = ['bash', str(script_path)]
        
        if repo_url:
            cmd.extend(['--repo', repo_url])
        if branch != 'gh-pages':
            cmd.extend(['--branch', branch])
        if latest_only:
            cmd.append('--latest-only')
        if dry_run:
            cmd.append('--dry-run')
        
        # Execute script
        result = subprocess.run(cmd, capture_output=False)
        
        if result.returncode == 0:
            return True, "Published to GitHub Pages successfully"
        else:
            return False, "Failed to publish to GitHub Pages"
    
    def get_publish_options(self) -> Dict[str, Dict]:
        """Get available publish options with descriptions"""
        return {
            'local': {
                'description': 'Start local HTTP server (LAN access)',
                'requires': [],
                'example': 'python src/main.py --mode daily --publish local'
            },
            'ngrok': {
                'description': 'Create public URL via ngrok tunnel',
                'requires': ['ngrok installed and authenticated'],
                'example': 'python src/main.py --mode daily --publish ngrok'
            },
            'github': {
                'description': 'Publish to GitHub Pages',
                'requires': ['Git', 'GitHub repo with write access'],
                'example': 'python src/main.py --mode daily --publish github --repo-url git@github.com:user/repo.git'
            }
        }


def add_publish_arguments(parser):
    """Add publish-related arguments to argument parser"""
    parser.add_argument(
        '--publish',
        choices=['local', 'ngrok', 'github'],
        help='Publish HTML reports after generation'
    )
    
    parser.add_argument(
        '--publish-port',
        type=int,
        default=8080,
        help='Port for local/ngrok server (default: 8080)'
    )
    
    parser.add_argument(
        '--repo-url',
        type=str,
        help='GitHub repository URL for publishing'
    )
    
    parser.add_argument(
        '--publish-branch',
        type=str,
        default='gh-pages',
        help='GitHub branch to publish to (default: gh-pages)'
    )
    
    parser.add_argument(
        '--latest-only',
        action='store_true',
        help='Only publish the latest report (for GitHub)'
    )
    
    parser.add_argument(
        '--no-browser',
        action='store_true',
        help='Do not open browser when serving locally'
    )


def handle_publish(
    publish_type: str,
    project_root: Path,
    port: int = 8080,
    repo_url: Optional[str] = None,
    branch: str = 'gh-pages',
    latest_only: bool = False,
    open_browser: bool = True
) -> Tuple[bool, str]:
    """
    Handle publishing based on type
    
    Args:
        publish_type: Type of publishing ('local', 'ngrok', 'github')
        project_root: Path to project root
        port: Port for local/ngrok
        repo_url: GitHub repo URL
        branch: GitHub branch
        latest_only: Only publish latest report
        open_browser: Open browser for local serving
        
    Returns:
        Tuple of (success, message)
    """
    publisher = ReportPublisher(project_root)
    
    if publish_type == 'local':
        return publisher.serve_local(port=port, open_browser=open_browser)
    elif publish_type == 'ngrok':
        return publisher.publish_ngrok(port=port)
    elif publish_type == 'github':
        return publisher.publish_github(
            repo_url=repo_url,
            branch=branch,
            latest_only=latest_only
        )
    else:
        return False, f"Unknown publish type: {publish_type}"


if __name__ == '__main__':
    # Demo/test
    project_root = Path(__file__).parent.parent.parent
    publisher = ReportPublisher(project_root)
    
    print("Available publish options:")
    for name, info in publisher.get_publish_options().items():
        print(f"\n  {name}:")
        print(f"    {info['description']}")
        print(f"    Requires: {', '.join(info['requires']) or 'None'}")
        print(f"    Example: {info['example']}")
    
    latest = publisher.get_latest_report()
    if latest:
        print(f"\nLatest report: {latest.name}")
    else:
        print("\nNo reports found. Run the analyzer first.")
