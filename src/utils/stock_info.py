"""
Stock Information Module
Provides stock name lookup functionality
"""

# Stock symbol to name mapping
STOCK_INFO = {
    # Tech Stocks
    'AAPL': 'Apple Inc.',
    'MSFT': 'Microsoft Corporation',
    'GOOGL': 'Alphabet Inc.',
    'AMZN': 'Amazon.com Inc.',
    'TSLA': 'Tesla Inc.',
    'NVDA': 'NVIDIA Corporation',
    'META': 'Meta Platforms Inc.',
    'NFLX': 'Netflix Inc.',
    'AMD': 'Advanced Micro Devices',
    'INTC': 'Intel Corporation',
    'DIS': 'The Walt Disney Company',
    'PYPL': 'PayPal Holdings Inc.',
    'ADBE': 'Adobe Inc.',
    'CRM': 'Salesforce Inc.',
    'CSCO': 'Cisco Systems Inc.',
    'NOW': 'ServiceNow Inc.',
    'INTU': 'Intuit Inc.',
    'GILD': 'Gilead Sciences Inc.',
    'QCOM': 'Qualcomm Inc.',
    'ORCL': 'Oracle Corporation',
    'AVGO': 'Broadcom Inc.',
    'SHOP': 'Shopify Inc.',
    'SNOW': 'Snowflake Inc.',
    'SQ': 'Block Inc.',
    'COIN': 'Coinbase Global Inc.',
    'BLOCK': 'Block Inc.',
    'ROKU': 'Roku Inc.',
    'PLTR': 'Palantir Technologies',
    'DDOG': 'Datadog Inc.',
    'RBLX': 'Roblox Corporation',
    'ZM': 'Zoom Video Communications',
    'UBER': 'Uber Technologies Inc.',
    'LYFT': 'Lyft Inc.',
    'TWTR': 'Twitter Inc.',
    'S': 'SentinelOne Inc.',
    'DOCU': 'DocuSign Inc.',
    'ZS': 'Zscaler Inc.',
    'CRWD': 'CrowdStrike Holdings',
    'OKTA': 'Okta Inc.',
    'TEAM': 'Atlassian Corporation',
    'WDAY': 'Workday Inc.',
    'ON': 'ON Semiconductor',
    
    # Financial Stocks
    'JPM': 'JPMorgan Chase & Co.',
    'BAC': 'Bank of America Corp',
    'WFC': 'Wells Fargo & Co',
    'GS': 'Goldman Sachs Group',
    'MS': 'Morgan Stanley',
    'BLK': 'BlackRock Inc.',
    'SCHW': 'Charles Schwab Corp',
    'C': 'Citigroup Inc.',
    'USB': 'U.S. Bancorp',
    'PNC': 'PNC Financial Services',
    'V': 'Visa Inc.',
    'MA': 'Mastercard Inc.',
    'AXP': 'American Express Co',
    'COF': 'Capital One Financial',
    'BK': 'Bank of New York Mellon',
    
    # Energy Stocks
    'XOM': 'Exxon Mobil Corp',
    'CVX': 'Chevron Corp',
    'COP': 'ConocoPhillips',
    'OXY': 'Occidental Petroleum',
    'SLB': 'Schlumberger NV',
    'MRO': 'Marathon Oil Corp',
    'VLO': 'Valero Energy Corp',
    'PSX': 'Phillips 66',
    'EOG': 'EOG Resources Inc',
    'HAL': 'Halliburton Co',
    'BKR': 'Baker Hughes Co',
    'FANG': 'Diamondback Energy',
    
    # Industrial Stocks
    'BA': 'Boeing Co',
    'LMT': 'Lockheed Martin Corp',
    'RTX': 'Raytheon Technologies',
    'GE': 'General Electric Co',
    'HON': 'Honeywell International',
    'MMM': '3M Company',
    'CAT': 'Caterpillar Inc.',
    'DE': 'Deere & Company',
    'UNP': 'Union Pacific Corp',
    'CSX': 'CSX Corporation',
    'NSC': 'Norfolk Southern Corp',
    'UPS': 'United Parcel Service',
    'FDX': 'FedEx Corporation',
    'NOC': 'Northrop Grumman Corp',
    'GD': 'General Dynamics Corp',
    'EMR': 'Emerson Electric Co',
    'ETN': 'Eaton Corporation',
    
    # Healthcare Stocks
    'PFE': 'Pfizer Inc.',
    'MRK': 'Merck & Co Inc',
    'ABT': 'Abbott Laboratories',
    'JNJ': 'Johnson & Johnson',
    'UNH': 'UnitedHealth Group',
    'CVS': 'CVS Health Corp',
    'WBA': 'Walgreens Boots Alliance',
    'LLY': 'Eli Lilly and Co',
    'TMO': 'Thermo Fisher Scientific',
    'ABBV': 'AbbVie Inc.',
    'BMY': 'Bristol-Myers Squibb',
    'AMGN': 'Amgen Inc.',
    'DHR': 'Danaher Corporation',
    'BAX': 'Baxter International',
    
    # Retail Stocks
    'WMT': 'Walmart Inc.',
    'TGT': 'Target Corporation',
    'COST': 'Costco Wholesale',
    'KR': 'Kroger Co.',
    'M': "Macy's Inc.",
    'KSS': "Kohl's Corporation",
    'JWN': 'Nordstrom Inc.',
    'BBY': 'Best Buy Co. Inc.',
    'HD': 'Home Depot Inc.',
    'LOW': "Lowe's Companies",
    'TJX': 'TJX Companies Inc.',
    'ROST': 'Ross Stores Inc.',
    'DLTR': 'Dollar Tree Inc.',
    'DG': 'Dollar General Corp',
    
    # Semiconductor Stocks
    'TXN': 'Texas Instruments',
    'NXPI': 'NXP Semiconductors',
    'ADI': 'Analog Devices Inc.',
    'MCHP': 'Microchip Technology',
    'SWKS': 'Skyworks Solutions',
    'KLAC': 'KLA Corporation',
    'LRCX': 'Lam Research Corp',
    'AMAT': 'Applied Materials Inc.',
    'TSM': 'Taiwan Semiconductor',
    'MU': 'Micron Technology',
    
    # Telecom & Utilities
    'VZ': 'Verizon Communications',
    'T': 'AT&T Inc.',
    'TMUS': 'T-Mobile US Inc.',
    'NEE': 'NextEra Energy Inc.',
    'DUK': 'Duke Energy Corp',
    'SO': 'Southern Company',
    'D': 'Dominion Energy Inc.',
    'EXC': 'Exelon Corporation',
    'AEP': 'American Electric Power',
    'SRE': 'Sempra Energy',
    
    # REITs
    'AMT': 'American Tower Corp',
    'PLD': 'Prologis Inc.',
    'CCI': 'Crown Castle Inc.',
    'O': 'Realty Income Corp',
    'STAG': 'STAG Industrial Inc.',
    'WPC': 'W.P. Carey Inc.',
    'VTR': 'Ventas Inc.',
    'VNQ': 'Vanguard Real Estate ETF',
    'SPG': 'Simon Property Group',
    'PSA': 'Public Storage',
    'EQIX': 'Equinix Inc.',
    'WELL': 'Welltower Inc.',
    'DLR': 'Digital Realty Trust',
    'AVB': 'AvalonBay Communities',
    'EQR': 'Equity Residential',
    
    # Auto Stocks
    'F': 'Ford Motor Company',
    'GM': 'General Motors Co',
    'STLA': 'Stellantis N.V.',
    'RIVN': 'Rivian Automotive',
    'LCID': 'Lucid Group Inc.',
    'NIO': 'NIO Inc.',
    'XPEV': 'XPeng Inc.',
    'LI': 'Li Auto Inc.',
    
    # Consumer Staples
    'KO': 'Coca-Cola Company',
    'PEP': 'PepsiCo Inc.',
    'PG': 'Procter & Gamble Co',
    'CL': 'Colgate-Palmolive Co',
    'KMB': 'Kimberly-Clark Corp',
    'K': 'Kellogg Company',
    'GIS': 'General Mills Inc.',
    'CAG': 'Conagra Brands Inc.',
    'SJM': 'JM Smucker Co',
    'HSY': 'Hershey Company',
    'MDLZ': 'Mondelez International',
    'STZ': 'Constellation Brands',
    
    # Other
    'BABA': 'Alibaba Group',
    'BIDU': 'Baidu Inc.',
    'JD': 'JD.com Inc.',
    'NKE': 'NIKE Inc.',
    'EBAY': 'eBay Inc.',
    'ETSY': 'Etsy Inc.',
    'W': 'Wayfair Inc.',
    'CHWY': 'Chewy Inc.',
    'PTON': 'Peloton Interactive',
}


def get_stock_name(symbol: str) -> str:
    """
    Get stock name by symbol
    
    Args:
        symbol: Stock ticker symbol
    
    Returns:
        Stock name or symbol if not found
    """
    return STOCK_INFO.get(symbol.upper(), symbol)


def get_all_symbols() -> list:
    """
    Get all known stock symbols
    
    Returns:
        List of stock symbols
    """
    return list(STOCK_INFO.keys())
