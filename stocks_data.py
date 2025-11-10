"""
Stock market data fetching using Yahoo Finance (yfinance)
No API key required!
"""
import os
from pathlib import Path
from datetime import datetime

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
        import yfinance as yf
    except ImportError:
        print("❌ yfinance not installed. Run: pip install yfinance")
        return []
    
    quotes = []
    
    print(f"📈 Fetching stock quotes for: {', '.join(STOCKS_SYMBOLS)}")
    
    for symbol in STOCKS_SYMBOLS:
        try:
            ticker = yf.Ticker(symbol)
            
            # Try fast_info first (faster, more reliable)
            try:
                fast_info = ticker.fast_info
                current_price = fast_info.get('lastPrice', 0)
                
                # Get more details from history for change calculation
                if current_price == 0:
                    # Fallback to history
                    hist = ticker.history(period='2d')
                    if not hist.empty:
                        current_price = hist['Close'].iloc[-1]
                        if len(hist) > 1:
                            prev_close = hist['Close'].iloc[-2]
                            change = current_price - prev_close
                            change_percent = (change / prev_close) * 100
                        else:
                            change = 0
                            change_percent = 0
                    else:
                        current_price = 0
                        change = 0
                        change_percent = 0
                else:
                    # Calculate change from previous close
                    prev_close = fast_info.get('previousClose', current_price)
                    change = current_price - prev_close
                    change_percent = (change / prev_close * 100) if prev_close != 0 else 0
                
            except Exception as e:
                print(f"  ⚠️  Fast info failed for {symbol}, trying full info: {e}")
                # Fallback to full info (slower but more complete)
                info = ticker.info
                
                if info.get('marketState') == 'PRE':
                    current_price = info.get('preMarketPrice', 0)
                    change_percent = info.get('preMarketChangePercent', 0)
                    change = info.get('preMarketChange', 0)
                else:
                    current_price = info.get('regularMarketPrice') or info.get('currentPrice', 0)
                    change = info.get('regularMarketChange', 0)
                    change_percent = info.get('regularMarketChangePercent', 0)
            
            # Get name (this requires full info, but it's optional)
            try:
                name = ticker.info.get('shortName', symbol)
            except:
                name = symbol
            
            quote = {
                'symbol': symbol,
                'price': current_price,
                'change': change,
                'change_percent': change_percent,
                'is_up': change >= 0,
                'name': name
            }
            
            quotes.append(quote)
            print(f"  {symbol}: ${current_price:.2f} ({change_percent:+.2f}%)")
            
        except Exception as e:
            print(f"  ⚠️  Error fetching {symbol}: {e}")
            # Add placeholder data so display doesn't break
            quotes.append({
                'symbol': symbol,
                'price': 0,
                'change': 0,
                'change_percent': 0,
                'is_up': True,
                'name': symbol,
                'error': True
            })
    
    return quotes


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

