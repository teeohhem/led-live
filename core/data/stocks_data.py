"""
Stock market data fetching using Yahoo Finance (yfinance).

Refactored to use base fetcher class and consolidate duplicate screener functions.

Key improvements:
- Single fetch_screener() method replaces 3 duplicate functions
- Async executor pattern encapsulated in base class
- Better error handling via retry logic
- Reduced code duplication by ~120 lines
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

import yfinance as yf

from .base_fetcher import DataFetcher

logger = logging.getLogger(__name__)

# Import configuration (loaded at startup via config.py)
from config import STOCKS_SYMBOLS, STOCKS_CHECK_INTERVAL


# ============================================================================
# Constants and Configuration
# ============================================================================

class ScreenerType(str, Enum):
    """Available stock screener types."""
    GAINERS = "day_gainers"
    LOSERS = "day_losers"
    MOST_ACTIVE = "most_actives"


# ============================================================================
# Stocks Data Fetcher
# ============================================================================

class StocksFetcher(DataFetcher[List[Dict[str, Any]]]):
    """
    Fetcher for Yahoo Finance stock data.
    
    Handles:
    - Individual stock quotes
    - Market screeners (gainers, losers, most active)
    - Market status
    
    Note: yfinance is synchronous, so we use executor for async compatibility.
    """
    
    def __init__(self, symbols: Optional[List[str]] = None, cache_ttl: int = 60):
        """
        Initialize stocks fetcher.
        
        Args:
            symbols: List of stock symbols to track (default: from config)
            cache_ttl: Cache time-to-live in seconds
        """
        super().__init__(cache_ttl=cache_ttl, logger_name='stocks_fetcher')
        self.symbols = symbols or STOCKS_SYMBOLS
    
    async def fetch(self) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch quotes for configured symbols (implements abstract method).
        
        Returns:
            List of stock quote dicts
        """
        return await self.fetch_quotes(self.symbols)
    
    async def _run_in_executor(self, func, *args):
        """
        Run blocking yfinance function in executor.
        
        Args:
            func: Blocking function to run
            *args: Arguments to pass to function
            
        Returns:
            Function result
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func, *args)
    
    async def fetch_quotes(self, symbols: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Fetch current stock quotes.
        
        Args:
            symbols: List of symbols to fetch (default: self.symbols)
            
        Returns:
            List of quote dicts with price, change, etc.
        """
        symbols = symbols or self.symbols
        self.logger.info(f"Fetching quotes for: {', '.join(symbols)}")
        
        try:
            # Run blocking yfinance call in executor
            tickers = await self._run_in_executor(
                lambda symbols: yf.Tickers(' '.join(symbols)),
                symbols
            )
            
            quotes = []
            for symbol in symbols:
                try:
                    ticker = tickers.tickers[symbol]
                    info = ticker.info
                    
                    # Get current price and change
                    current_price = info.get('regularMarketPrice') or info.get('currentPrice', 0)
                    change = info.get('regularMarketChange', 0)
                    change_percent = float(info.get('regularMarketChangePercent', 0))
                    
                    quote = {
                        'symbol': symbol,
                        'price': current_price,
                        'change': change,
                        'change_percent': change_percent,
                        'is_up': change >= 0,
                        'name': info.get('shortName', symbol)
                    }
                    
                    quotes.append(quote)
                    self.logger.debug(f"{symbol}: ${current_price:.2f} ({change_percent:+.2f}%)")
                    
                except Exception as e:
                    self.logger.warning(f"Error parsing {symbol}: {e}")
                    # Add placeholder
                    quotes.append({
                        'symbol': symbol,
                        'price': 0,
                        'change': 0,
                        'change_percent': 0,
                        'is_up': False,
                        'name': symbol
                    })
            
            self.logger.info(f"Fetched {len(quotes)} stock quotes")
            return quotes
            
        except Exception as e:
            self.logger.error(f"Error fetching stock quotes: {e}")
            return []
    
    async def fetch_screener(
        self, 
        screener_type: ScreenerType, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Fetch stocks from yfinance screener.
        
        This single method replaces:
        - fetch_market_gainers()
        - fetch_market_losers()
        - fetch_market_active()
        
        Args:
            screener_type: Type of screener (GAINERS, LOSERS, MOST_ACTIVE)
            limit: Maximum number of stocks to return
            
        Returns:
            List of stock quote dicts
        """
        self.logger.info(f"Fetching {screener_type.value} (limit: {limit})...")
        
        try:
            # Run blocking yfinance screener call in executor
            response = await self._run_in_executor(
                lambda: yf.screen(screener_type.value, count=limit)
            )
            
            if not response or 'quotes' not in response:
                self.logger.warning(f"No data returned from {screener_type.value} screener")
                return []
            
            quotes_data = response['quotes']
            self.logger.debug(f"Screener returned {len(quotes_data)} results")
            
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
                    self.logger.debug(
                        f"Error parsing {quote_data.get('symbol', 'unknown')}: {e}"
                    )
                    continue
            
            # Log summary
            if screener_type == ScreenerType.GAINERS:
                summary = ', '.join([f"{q['symbol']} +{q['change_percent']:.1f}%" for q in quotes[:5]])
            elif screener_type == ScreenerType.LOSERS:
                summary = ', '.join([f"{q['symbol']} {q['change_percent']:.1f}%" for q in quotes[:5]])
            else:
                summary = ', '.join([f"{q['symbol']}" for q in quotes[:5]])
            
            self.logger.info(f"Top {len(quotes)} {screener_type.value}: {summary}...")
            
            return quotes
            
        except Exception as e:
            self.logger.error(f"Error fetching {screener_type.value}: {e}")
            return []
    
    async def fetch_mixed_screener(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch a mix of top gainers and losers.
        
        Args:
            limit: Total number of stocks to return
            
        Returns:
            List alternating gainers and losers
        """
        half = limit // 2
        gainers = await self.fetch_screener(ScreenerType.GAINERS, half)
        losers = await self.fetch_screener(ScreenerType.LOSERS, limit - half)
        
        # Interleave gainers and losers
        mixed = []
        for i in range(max(len(gainers), len(losers))):
            if i < len(gainers):
                mixed.append(gainers[i])
            if i < len(losers):
                mixed.append(losers[i])
        
        self.logger.info(f"Mixed market data: {len(mixed)} stocks (gainers + losers)")
        return mixed
    
    @staticmethod
    def get_market_status() -> str:
        """
        Determine if market is open or closed.
        
        Returns:
            "open", "closed", or "pre-market"
            
        Note:
            Simplified version - doesn't account for holidays or timezone differences.
            Market hours: 9:30 AM - 4:00 PM EST
        """
        now = datetime.now()
        weekday = now.weekday()  # 0=Monday, 6=Sunday
        hour = now.hour
        minute = now.minute
        
        # Weekend
        if weekday >= 5:  # Saturday or Sunday
            return "closed"
        
        # Weekday - check time (EST)
        if (hour == 9 and minute >= 30) or (hour >= 10 and hour < 16):
            return "open"
        elif hour >= 4 and hour < 9:
            return "pre-market"
        elif hour == 9 and minute < 30:
            return "pre-market"
        else:
            return "closed"


# ============================================================================
# Module-level API - use StocksFetcher class directly
# ============================================================================

# For convenience, create module-level fetcher instance
stocks_fetcher = StocksFetcher(cache_ttl=60)
