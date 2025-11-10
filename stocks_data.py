"""
Stock market data fetching using Yahoo Finance (yfinance)
No API key required!
"""
import os
from pathlib import Path
from datetime import datetime
import asyncio

# Load environment variables from config.env if it exists
config_file = Path(__file__).parent / "config.env"
if config_file.exists():
    with open(config_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip())

# --- Settings ---
STOCKS_SYMBOLS = [s.strip() for s in os.getenv("STOCKS_SYMBOLS", "AAPL,GOOGL,MSFT,TSLA").split(",") if s.strip()]
STOCKS_CHECK_INTERVAL = int(os.getenv("STOCKS_CHECK_INTERVAL", "300"))  # 5 minutes default


def _fetch_quote_sync(symbol):
    """
    Synchronous function to fetch a single stock quote.
    Called from thread pool to avoid blocking async event loop.
    """
    import yfinance as yf  # Import here to avoid issues with thread pool
    from datetime import datetime as dt
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # Debug: print timestamp and what we're fetching
        fetch_time = dt.now().strftime('%H:%M:%S')
        print(f"  [{fetch_time}] Fetching {symbol}...")
        
        # Check market state to determine which price to use
        market_state = info.get('marketState', 'REGULAR')
        
        # Debug: show what's available
        pre_price = info.get('preMarketPrice')
        reg_price = info.get('regularMarketPrice')
        cur_price = info.get('currentPrice')
        
        if market_state == 'PRE' and pre_price:
            # Use pre-market data
            current_price = pre_price
            change = info.get('preMarketChange', 0)
            change_percent = info.get('preMarketChangePercent', 0)
            source = "PRE"
        elif reg_price:
            # Use regular market data
            current_price = reg_price
            change = info.get('regularMarketChange', 0)
            change_percent = info.get('regularMarketChangePercent', 0)
            source = "REG"
        elif cur_price:
            # Fallback to current price
            current_price = cur_price
            change = info.get('regularMarketChange', 0)
            change_percent = info.get('regularMarketChangePercent', 0)
            source = "CUR"
        else:
            current_price = 0
            change = 0
            change_percent = 0
            source = "NONE"
        
        # Get company name
        name = info.get('shortName') or info.get('longName') or symbol
        
        quote = {
            'symbol': symbol,
            'price': current_price,
            'change': change,
            'change_percent': change_percent,
            'is_up': change >= 0,
            'name': name,
            'market_state': market_state
        }
        
        # Debug print with source and available prices
        print(f"  {symbol}: ${current_price:.2f} ({change_percent:+.2f}%) [state={market_state}, source={source}]")
        if pre_price and reg_price and pre_price != reg_price:
            print(f"    Available: PRE=${pre_price:.2f}, REG=${reg_price:.2f}")
        
        return quote
    except Exception as e:
        print(f"  ⚠️  Error fetching {symbol}: {e}")
        # Return placeholder data
        return {
            'symbol': symbol,
            'price': 0,
            'change': 0,
            'change_percent': 0,
            'is_up': False,
            'name': symbol,
            'market_state': 'CLOSED'
        }


async def fetch_stock_quotes():
    """
    Fetch current stock quotes using yfinance.
    
    Returns:
        List of dicts with stock data:
        [
            {
                'symbol': 'AAPL',
                'price': 185.50,
                'change': 2.50,
                'change_percent': 1.37,
                'is_up': True
            },
            ...
        ]
    """
    try:
        import yfinance as yf  # Just to check it's installed
    except ImportError:
        print("❌ yfinance not installed. Run: pip install yfinance")
        return []
    
    print(f"📈 Fetching stock quotes for: {', '.join(STOCKS_SYMBOLS)}")
    
    # Run synchronous yfinance calls in thread pool to avoid blocking async event loop
    loop = asyncio.get_event_loop()
    tasks = []
    
    for symbol in STOCKS_SYMBOLS:
        # Run each stock fetch in a thread pool
        task = loop.run_in_executor(None, _fetch_quote_sync, symbol)
        tasks.append(task)
    
    # Wait for all fetches to complete (runs in parallel)
    quotes = await asyncio.gather(*tasks)
    
    return list(quotes)


def get_market_status():
    """
    Determine if market is open or closed.
    
    Returns:
        str: "open", "closed", or "pre-market"
    """
    now = datetime.now()
    weekday = now.weekday()  # 0=Monday, 6=Sunday
    hour = now.hour
    minute = now.minute
    
    # Weekend
    if weekday >= 5:  # Saturday or Sunday
        return "closed"
    
    # Weekday - check time (EST)
    # Market hours: 9:30 AM - 4:00 PM EST
    # Pre-market: 4:00 AM - 9:30 AM EST
    # After-hours: 4:00 PM - 8:00 PM EST
    
    # This is a simplified version - doesn't account for holidays
    # or timezone differences
    
    if (hour == 9 and minute >= 30) or (hour >= 10 and hour < 16):
        return "open"
    elif hour >= 4 and hour < 9:
        return "pre-market"
    elif hour == 9 and minute < 30:
        return "pre-market"
    else:
        return "closed"


if __name__ == "__main__":
    # Test the module
    import asyncio
    
    async def test():
        quotes = await fetch_stock_quotes()
        print(f"\n📊 Fetched {len(quotes)} quotes:")
        for q in quotes:
            status = "▲" if q['is_up'] else "▼"
            color = "green" if q['is_up'] else "red"
            print(f"  {q['symbol']:6} ${q['price']:8.2f}  {status} {q['change_percent']:+.2f}%")
        
        print(f"\n🕐 Market status: {get_market_status()}")
    
    asyncio.run(test())

