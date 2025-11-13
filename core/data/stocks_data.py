"""
Stock market data fetching using Yahoo Finance (yfinance)
No API key required!
"""
import os
from pathlib import Path
from datetime import datetime
import asyncio
import logging
import yfinance as yf
logger = logging.getLogger(__name__)

# Import configuration (loaded at startup via config.py)
from config import STOCKS_SYMBOLS, STOCKS_CHECK_INTERVAL


async def fetch_stock_quotes():
    """
    Fetch current stock quotes using yfinance.Tickers() (much simpler!).
    
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
    logger.info(f"Fetching quotes for: {', '.join(STOCKS_SYMBOLS)}")
    
    try:
        # Run in executor to avoid blocking async loop
        tickers = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: yf.Tickers(' '.join(STOCKS_SYMBOLS))
        )
        
        quotes = []
        for symbol in STOCKS_SYMBOLS:
            try:
                ticker = tickers.tickers[symbol]
                info = ticker.info
                
                # Get current price and change
                current_price = info.get('regularMarketPrice') or info.get('currentPrice', 0)
                change = info.get('regularMarketChange', 0)
                change_percent = info.get('regularMarketChangePercent', 0)
                
                quote = {
                    'symbol': symbol,
                    'price': current_price,
                    'change': change,
                    'change_percent': change_percent,
                    'is_up': change >= 0,
                    'name': info.get('shortName', symbol)
                }
                
                quotes.append(quote)
                logger.debug(f"{symbol}: ${current_price:.2f} ({change_percent:+.2f}%)")
                
            except Exception as e:
                logger.warning(f"Error parsing {symbol}: {e}")
                # Add placeholder
                quotes.append({
                    'symbol': symbol,
                    'price': 0,
                    'change': 0,
                    'change_percent': 0,
                    'is_up': False,
                    'name': symbol
                })
        
        logger.info(f"Fetched {len(quotes)} stock quotes")
        return quotes
        
    except Exception as e:
        logger.error(f"Error fetching stock quotes: {e}")
        return []


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
        logger.debug(f"\nFetched{len(quotes)}quotes:")
        for q in quotes:
            status = "▲" if q['is_up'] else "▼"
            color = "green" if q['is_up'] else "red"
            logger.info(f"{q['symbol']:6}${q['price']:8.2f}{status}{q['change_percent']:+.2f}%")
        
        logger.debug(f"\nMarketstatus:{get_market_status()}")
    
    asyncio.run(test())


# ============================================================================
# MARKET DATA FOR TICKER MODE
# ============================================================================

async def fetch_market_gainers(limit=10):
    """
    Fetch top gaining stocks today using yfinance screener API.
    
    Args:
        limit: Maximum number of stocks to return (max 250)
    
    Returns:
        List of stock quote dicts sorted by % gain
    """
    
    try:
        logger.info(f"Fetching top {limit} gainers from yfinance screener...")
        
        # Use yfinance predefined screener for day_gainers
        # Run in executor to avoid blocking async loop
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: yf.screen("day_gainers", count=limit)
        )
        
        if not response or 'quotes' not in response:
            logger.warning("No gainers data returned from screener")
            return []
        
        quotes_data = response['quotes']
        logger.info(f"Screener returned {len(quotes_data)} gainers")
        
        # Convert to our quote format
        quotes = []
        for quote_data in quotes_data[:limit]:
            try:
                symbol = quote_data.get('symbol', '')
                price = quote_data.get('regularMarketPrice', 0)
                change_pct = quote_data.get('regularMarketChangePercent', 0)
                
                quotes.append({
                    'symbol': symbol,
                    'price': price,
                    'change_percent': change_pct,
                    'is_up': change_pct > 0
                })
            except Exception as e:
                logger.debug(f"Error parsing gainer {quote_data.get('symbol', 'unknown')}: {e}")
                continue
        
        gainer_list = ', '.join([f"{q['symbol']} +{q['change_percent']:.1f}%" for q in quotes[:5]])
        logger.info(f"Top {len(quotes)} gainers: {gainer_list}...")
        
        return quotes
    except Exception as e:
        logger.error(f"Error fetching market gainers: {e}")
        return []


async def fetch_market_losers(limit=10):
    """
    Fetch top losing stocks today using yfinance screener API.
    
    Args:
        limit: Maximum number of stocks to return (max 250)
    
    Returns:
        List of stock quote dicts sorted by % loss
    """
    
    try:
        logger.info(f"Fetching top {limit} losers from yfinance screener...")
        
        # Use yfinance predefined screener for day_losers
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: yf.screen("day_losers", count=limit)
        )
        
        if not response or 'quotes' not in response:
            logger.warning("No losers data returned from screener")
            return []
        
        quotes_data = response['quotes']
        logger.info(f"Screener returned {len(quotes_data)} losers")
        
        # Convert to our quote format
        quotes = []
        for quote_data in quotes_data[:limit]:
            try:
                symbol = quote_data.get('symbol', '')
                price = quote_data.get('regularMarketPrice', 0)
                change_pct = quote_data.get('regularMarketChangePercent', 0)
                
                quotes.append({
                    'symbol': symbol,
                    'price': price,
                    'change_percent': change_pct,
                    'is_up': change_pct > 0
                })
            except Exception as e:
                logger.debug(f"Error parsing loser {quote_data.get('symbol', 'unknown')}: {e}")
                continue
        
        loser_list = ', '.join([f"{q['symbol']} {q['change_percent']:.1f}%" for q in quotes[:5]])
        logger.info(f"Top {len(quotes)} losers: {loser_list}...")
        
        return quotes
    except Exception as e:
        logger.error(f"Error fetching market losers: {e}")
        return []


async def fetch_market_active(limit=10):
    """
    Fetch most actively traded stocks using yfinance screener API.
    
    Args:
        limit: Maximum number of stocks to return (max 250)
    
    Returns:
        List of stock quote dicts sorted by volume
    """
    
    try:
        logger.info(f"Fetching top {limit} most active from yfinance screener...")
        
        # Use yfinance predefined screener for most_actives
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: yf.screen("most_actives", count=limit)
        )
        
        if not response or 'quotes' not in response:
            logger.warning("No active stocks data returned from screener")
            return []
        
        quotes_data = response['quotes']
        logger.info(f"Screener returned {len(quotes_data)} most active stocks")
        
        # Convert to our quote format
        quotes = []
        for quote_data in quotes_data[:limit]:
            try:
                symbol = quote_data.get('symbol', '')
                price = quote_data.get('regularMarketPrice', 0)
                change_pct = quote_data.get('regularMarketChangePercent', 0)
                
                quotes.append({
                    'symbol': symbol,
                    'price': price,
                    'change_percent': change_pct,
                    'is_up': change_pct > 0
                })
            except Exception as e:
                logger.debug(f"Error parsing active stock {quote_data.get('symbol', 'unknown')}: {e}")
                continue
        
        active_list = ', '.join([f"{q['symbol']}" for q in quotes[:5]])
        logger.info(f"Top {len(quotes)} most active: {active_list}...")
        
        return quotes
    except Exception as e:
        logger.error(f"Error fetching most active stocks: {e}")
        return []


async def fetch_market_mixed(limit=10):
    """
    Fetch a mix of top gainers and losers.
    
    Args:
        limit: Total number of stocks to return
    
    Returns:
        List alternating gainers and losers
    """
    half = limit // 2
    gainers = await fetch_market_gainers(half)
    losers = await fetch_market_losers(limit - half)
    
    # Interleave gainers and losers
    mixed = []
    for i in range(max(len(gainers), len(losers))):
        if i < len(gainers):
            mixed.append(gainers[i])
        if i < len(losers):
            mixed.append(losers[i])
    
    logger.info(f"Mixed market data: {len(mixed)} stocks (gainers + losers)")
    return mixed

