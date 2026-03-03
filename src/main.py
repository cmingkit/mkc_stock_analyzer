#!/usr/bin/env python3
"""
Stock Analyzer - Main Entry Point
Analyzes Reddit sentiment, tracks prices, and generates reports
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import yaml

from src.collectors.reddit_collector import RedditCollector
from src.collectors.price_collector import PriceCollector
from src.analyzers.sentiment_analyzer import SentimentAnalyzer
from src.analyzers.technical_analyzer import TechnicalAnalyzer
from src.analyzers.risk_analyzer import RiskAnalyzer
from src.reporters.html_reporter import HTMLReporter
from src.reporters.pdf_reporter import PDFReporter
from src.reporters.telegram_sender import TelegramSender
from src.utils.config_loader import ConfigLoader, get_config
from src.utils.logger import setup_logger, get_logger
from src.utils.stock_info import STOCK_INFO
from src.utils.publisher import ReportPublisher, handle_publish

# Project root
PROJECT_ROOT = Path(__file__).parent.parent


def load_stocks_yaml() -> Dict[str, List[str]]:
    """Load stock categories from YAML file"""
    stocks_file = PROJECT_ROOT / 'config' / 'stocks.yaml'
    if stocks_file.exists():
        with open(stocks_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    return {}


def get_all_stocks() -> Set[str]:
    """Get all stock symbols from config and built-in list"""
    stocks = set(STOCK_INFO.keys())
    
    # Add from stocks.yaml
    stocks_yaml = load_stocks_yaml()
    for category, symbols in stocks_yaml.items():
        if isinstance(symbols, list):
            stocks.update(symbols)
    
    return stocks


def get_undervalued_symbols() -> Set[str]:
    """Get symbols for undervalued analysis"""
    stocks_yaml = load_stocks_yaml()
    
    undervalued_categories = {
        'financial', 'energy', 'industrial', 'healthcare',
        'retail', 'telecom_utility', 'reits', 'auto', 'consumer', 'undervalued'
    }
    
    symbols = set()
    for category, syms in stocks_yaml.items():
        if category in undervalued_categories and isinstance(syms, list):
            symbols.update(syms)
    
    return symbols


def run_daily_analysis(
    config: ConfigLoader,
    verbose: bool = False,
    stocks: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Run daily analysis
    
    Args:
        config: Configuration loader
        verbose: Enable verbose output
        stocks: Specific stocks to analyze (optional)
    
    Returns:
        Analysis results
    """
    log = get_logger('main')
    log.info("=" * 60)
    log.info("Starting Daily Stock Analysis")
    log.info("=" * 60)
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'mode': 'daily'
    }
    
    # Get stock symbols
    all_stocks = get_all_stocks()
    if stocks:
        all_stocks = all_stocks & set(stocks)
    
    undervalued_symbols = get_undervalued_symbols()
    
    # 1. Collect Reddit data
    log.info("Step 1: Collecting Reddit data...")
    reddit_collector = RedditCollector({
        'subreddits': config.get('collection.reddit.subreddits'),
        'hot_posts_limit': config.get('collection.reddit.hot_posts_limit', 30),
        'rate_limit_delay': config.get('collection.reddit.rate_limit_delay', 1.0),
        'known_stocks': all_stocks,
        'reddit_client_id': config.get_secret('reddit.client_id'),
        'reddit_client_secret': config.get_secret('reddit.client_secret'),
        'reddit_user_agent': config.get_secret('reddit.user_agent')
    })
    reddit_data = reddit_collector.collect()
    results['reddit_data'] = reddit_data
    
    # 2. Collect price data first (needed for sentiment analysis enrichment)
    log.info("Step 2: Collecting price data...")
    
    price_collector = PriceCollector({
        'providers': config.get('collection.price.providers', ['yfinance']),
        'cache_ttl': config.get('collection.price.cache_ttl', 3600),
        'yahoo_api_delay': config.get('collection.price.yahoo_api_delay', 2.0),
        'alpha_vantage_api_key': config.get_secret('alpha_vantage.api_key')
    })
    # Collect price data for all known stocks (limited to avoid rate limits)
    initial_price_data = price_collector.collect(list(all_stocks)[:50], days=config.get('analysis.history_days', 90))
    
    # 3. Analyze sentiment with price data enrichment
    log.info("Step 3: Analyzing sentiment...")
    sentiment_analyzer = SentimentAnalyzer({
        'top_stocks': config.get('analysis.top_stocks', 15),
        'risk_threshold': config.get('analysis.risk_threshold', 0.7)
    })
    sentiment_results = sentiment_analyzer.analyze(reddit_data, initial_price_data)
    results['sentiment_analysis'] = sentiment_results
    
    # 4. Collect additional price data for top stocks
    log.info("Step 4: Updating price data for top stocks...")
    top_tickers = [s['ticker'] for s in sentiment_results.get('top_stocks', [])]
    
    # Merge price data
    price_data = initial_price_data
    missing_tickers = [t for t in top_tickers if t not in price_data.get('price_data', {})]
    if missing_tickers:
        additional_price_data = price_collector.collect(missing_tickers, days=config.get('analysis.history_days', 90))
        price_data['price_data'].update(additional_price_data.get('price_data', {}))
    
    results['price_data'] = price_data
    
    # 5. Technical analysis
    log.info("Step 5: Performing technical analysis...")
    technical_analyzer = TechnicalAnalyzer()
    technical_results = technical_analyzer.analyze(price_data)
    results['technical_analysis'] = technical_results
    
    # 6. Risk and undervalued analysis
    log.info("Step 6: Analyzing risk and undervalued stocks...")
    risk_analyzer = RiskAnalyzer({
        'undervalued_threshold': config.get('analysis.risk_threshold', 60)
    })
    risk_results = risk_analyzer.analyze(
        reddit_data, 
        price_data, 
        technical_results,
        undervalued_symbols
    )
    results['risk_analysis'] = risk_results
    
    log.info("Analysis complete!")
    
    return results


def run_alerts_mode(config: ConfigLoader, stocks: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Run alerts mode (quick price check)
    
    Args:
        config: Configuration loader
        stocks: Specific stocks to check
    
    Returns:
        Alert results
    """
    log = get_logger('main')
    log.info("Running alerts mode...")
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'mode': 'alerts',
        'alerts': []
    }
    
    # Get stocks to check
    stocks_to_check = stocks or list(get_all_stocks())[:20]
    
    # Collect prices
    price_collector = PriceCollector({
        'providers': config.get('collection.price.providers', ['yfinance'])
    })
    price_data = price_collector.collect(stocks_to_check, days=7)
    
    # Check for significant changes
    for ticker, data in price_data.get('price_data', {}).items():
        history = data.get('history', [])
        if len(history) >= 2:
            current = history[-1][1]
            previous = history[-2][1]
            change_pct = (current - previous) / previous * 100
            
            if abs(change_pct) > 5:
                results['alerts'].append({
                    'ticker': ticker,
                    'type': 'price_change',
                    'change_pct': change_pct,
                    'current_price': current
                })
    
    return results


def generate_reports(
    results: Dict[str, Any],
    config: ConfigLoader,
    formats: List[str] = None,
    send_telegram: bool = True,
    output_dir: Optional[str] = None
) -> Dict[str, str]:
    """
    Generate reports from analysis results
    
    Args:
        results: Analysis results
        config: Configuration loader
        formats: Report formats to generate
        send_telegram: Whether to send via Telegram
        output_dir: Custom output directory (for GitHub Pages)
    
    Returns:
        Dictionary of format -> file path
    """
    log = get_logger('main')
    log.info("Generating reports...")
    
    formats = formats or config.get('report.formats', ['html', 'json'])
    output_files = {}
    
    # Determine output directory
    if output_dir:
        base_output_dir = Path(output_dir)
        base_output_dir.mkdir(parents=True, exist_ok=True)
    else:
        base_output_dir = PROJECT_ROOT / 'reports' / 'html'
        base_output_dir.mkdir(parents=True, exist_ok=True)
    
    # HTML report
    if 'html' in formats:
        html_reporter = HTMLReporter({
            'template_dir': str(PROJECT_ROOT / 'templates'),
            'output_dir': str(base_output_dir),
            'for_github_pages': output_dir is not None  # Flag for GitHub Pages
        })
        html_path = html_reporter.generate(results)
        output_files['html'] = html_path
        log.info(f"HTML report: {html_path}")
    
    # PDF report
    if 'pdf' in formats:
        pdf_reporter = PDFReporter({
            'template_dir': str(PROJECT_ROOT / 'templates'),
            'output_dir': str(PROJECT_ROOT / 'reports' / 'pdf')
        })
        pdf_path = pdf_reporter.generate(results)
        if pdf_path:
            output_files['pdf'] = pdf_path
            log.info(f"PDF report: {pdf_path}")
    
    # JSON report
    if 'json' in formats:
        json_dir = PROJECT_ROOT / 'reports' / 'json'
        json_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        json_path = json_dir / f'report_{timestamp}.json'
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        output_files['json'] = str(json_path)
        log.info(f"JSON report: {json_path}")
    
    # Telegram
    if send_telegram:
        telegram = TelegramSender({
            'bot_token': config.get_secret('telegram.bot_token'),
            'chat_id': config.get_secret('telegram.chat_id')
        })
        success = telegram.generate(results)
        if success:
            log.info("Telegram message sent")
        else:
            log.warning("Failed to send Telegram message")
    
    return output_files


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Stock Analyzer - Analyze Reddit sentiment and stock prices'
    )
    
    parser.add_argument(
        '--mode',
        choices=['daily', 'alerts', 'weekly'],
        default='daily',
        help='Analysis mode (default: daily)'
    )
    
    parser.add_argument(
        '--format',
        nargs='+',
        choices=['html', 'pdf', 'json'],
        default=['html', 'json'],
        help='Report formats to generate'
    )
    
    parser.add_argument(
        '--stocks',
        nargs='+',
        help='Specific stocks to analyze'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration file'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--no-telegram',
        action='store_true',
        help='Skip sending Telegram message'
    )
    
    # GitHub Pages support
    parser.add_argument(
        '--output-dir',
        type=str,
        help='Custom output directory for reports (e.g., docs/reports for GitHub Pages)'
    )
    
    # Publish options
    parser.add_argument(
        '--publish',
        choices=['local', 'ngrok', 'github'],
        help='Publish HTML reports after generation (local/ngrok/github)'
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
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = 'DEBUG' if args.verbose else 'INFO'
    setup_logger(level=log_level, log_file='logs/app.log')
    log = get_logger('main')
    
    try:
        # Load configuration
        if args.config:
            config = ConfigLoader(settings_path=args.config)
        else:
            config = get_config()
        
        # Run analysis based on mode
        if args.mode == 'daily':
            results = run_daily_analysis(config, args.verbose, args.stocks)
        elif args.mode == 'alerts':
            results = run_alerts_mode(config, args.stocks)
        elif args.mode == 'weekly':
            results = run_daily_analysis(config, args.verbose, args.stocks)
        
        # Generate reports
        output_files = generate_reports(
            results, 
            config,
            formats=args.format,
            send_telegram=not args.no_telegram,
            output_dir=args.output_dir
        )
        
        # Print summary
        print("\n" + "=" * 60)
        print("Analysis Complete!")
        print("=" * 60)
        
        if results.get('sentiment_analysis', {}).get('top_stocks'):
            print("\n🔥 Top Mentioned Stocks:")
            for stock in results['sentiment_analysis']['top_stocks'][:5]:
                print(f"  {stock['sentiment_emoji']} {stock['ticker']}: {stock['count']} mentions")
        
        if results.get('risk_analysis', {}).get('undervalued_stocks'):
            print("\n💎 Undervalued Picks:")
            for stock in results['risk_analysis']['undervalued_stocks'][:3]:
                print(f"  {stock['label']} {stock['ticker']}: Score {stock['score']:.0f}")
        
        print(f"\nReports generated:")
        for fmt, path in output_files.items():
            print(f"  {fmt.upper()}: {path}")
        
        print("\n✅ Done!")
        
        # Handle publishing
        if args.publish:
            print(f"\n{'='*60}")
            print(f"Publishing reports via {args.publish}...")
            print(f"{'='*60}")
            
            success, message = handle_publish(
                publish_type=args.publish,
                project_root=PROJECT_ROOT,
                port=args.publish_port,
                repo_url=args.repo_url,
                branch=args.publish_branch,
                latest_only=args.latest_only,
                open_browser=not args.no_browser
            )
            
            if not success:
                print(f"\n❌ Publish failed: {message}")
                return 1
        
    except Exception as e:
        log.error(f"Analysis failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
