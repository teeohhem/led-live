"""
Unit tests for StocksFetcher.
"""
import pytest
import os
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, time

from core.data.stocks_data import StocksFetcher, ScreenerType


@pytest.mark.asyncio
class TestStocksFetcher:
    """Test cases for StocksFetcher."""
    
    async def test_initialization(self):
        """Test initialization with default parameters."""
        with patch.dict(os.environ, {'STOCKS_SYMBOLS': 'AAPL,GOOGL,MSFT'}):
            fetcher = StocksFetcher()
            
            assert fetcher._cache_ttl == 60
            assert 'AAPL' in fetcher.symbols or len(fetcher.symbols) > 0
    
    async def test_initialization_with_custom_symbols(self):
        """Test initialization with custom symbol list."""
        fetcher = StocksFetcher(
            symbols=['TSLA', 'NVDA'],
            cache_ttl=120
        )
        
        assert fetcher.symbols == ['TSLA', 'NVDA']
        assert fetcher._cache_ttl == 120
    
    async def test_get_market_status_weekend(self):
        """Test market status on weekend."""
        with patch('core.data.stocks_data.datetime') as mock_dt:
            mock_now = MagicMock()
            mock_now.weekday.return_value = 5  # Saturday
            mock_dt.now.return_value = mock_now
            
            status = StocksFetcher.get_market_status()
            assert status == 'closed'
    
    @patch('core.data.stocks_data._YFINANCE_AVAILABLE', True)
    @patch('core.data.stocks_data.yf')
    async def test_fetch_quotes(self, mock_yf):
        """Test fetching stock quotes."""
        # Mock yfinance Ticker response
        mock_ticker = MagicMock()
        mock_ticker.info = {
            'symbol': 'AAPL',
            'regularMarketPrice': 195.50,
            'regularMarketChange': 4.25,
            'regularMarketChangePercent': 2.22
        }
        mock_yf.Ticker.return_value = mock_ticker
        
        fetcher = StocksFetcher(symbols=['AAPL'])
        result = await fetcher.fetch_quotes(['AAPL'])
        
        assert len(result) > 0
        assert result[0]['symbol'] == 'AAPL'
    
    @patch('core.data.stocks_data._YFINANCE_AVAILABLE', True)
    @patch('core.data.stocks_data.yf')
    async def test_fetch_screener_losers(self, mock_yf):
        """Test fetching top losers."""
        mock_yf.screen.return_value = {
            'quotes': [
                {
                    'symbol': 'TEST',
                    'regularMarketPrice': 100.0,
                    'regularMarketChange': -5.0,
                    'regularMarketChangePercent': -4.76
                }
            ]
        }
        
        fetcher = StocksFetcher()
        result = await fetcher.fetch_screener(ScreenerType.LOSERS, limit=5)
        
        assert isinstance(result, list)
    
    @patch('core.data.stocks_data._YFINANCE_AVAILABLE', True)
    @patch('core.data.stocks_data.yf')
    async def test_fetch_screener_most_active(self, mock_yf):
        """Test fetching most active stocks."""
        mock_yf.screen.return_value = {'quotes': []}
        
        fetcher = StocksFetcher()
        result = await fetcher.fetch_screener(ScreenerType.MOST_ACTIVE, limit=5)
        
        assert isinstance(result, list)
    
    @patch('core.data.stocks_data.StocksFetcher.fetch_screener')
    async def test_fetch_mixed_screener(self, mock_screener):
        """Test fetching mixed gainers and losers."""
        mock_screener.side_effect = [
            [{'symbol': 'TSLA', 'change_percent': 5.0}],  # Gainers
            [{'symbol': 'F', 'change_percent': -3.0}]      # Losers
        ]
        
        fetcher = StocksFetcher()
        result = await fetcher.fetch_mixed_screener(limit=10)
        
        # Should call screener twice (gainers and losers)
        assert mock_screener.call_count == 2
        assert isinstance(result, list)
    
    async def test_screener_type_enum(self):
        """Test ScreenerType enum values."""
        assert ScreenerType.GAINERS.value == 'day_gainers'
        assert ScreenerType.LOSERS.value == 'day_losers'
        assert ScreenerType.MOST_ACTIVE.value == 'most_actives'
    
    @patch('core.data.stocks_data._YFINANCE_AVAILABLE', True)
    @patch('core.data.stocks_data.yf')
    async def test_caching_behavior(self, mock_yf):
        """Test that quotes are cached properly."""
        mock_ticker = MagicMock()
        mock_ticker.info = {
            'symbol': 'AAPL',
            'regularMarketPrice': 195.50,
            'regularMarketChange': 4.25,
            'regularMarketChangePercent': 2.22
        }
        mock_yf.Ticker.return_value = mock_ticker
        
        fetcher = StocksFetcher(symbols=['AAPL'])
        
        # First call
        result1 = await fetcher.get_cached_or_fetch()
        call_count_1 = mock_yf.Ticker.call_count
        
        # Second call should use cache
        result2 = await fetcher.get_cached_or_fetch()
        call_count_2 = mock_yf.Ticker.call_count
        
        # Should not fetch again
        assert call_count_2 == call_count_1
    
    @patch('core.data.stocks_data._YFINANCE_AVAILABLE', True)
    @patch('core.data.stocks_data.yf')
    async def test_screener_limit_parameter(self, mock_yf):
        """Test that screener respects limit parameter."""
        # Create more quotes than the limit
        many_quotes = {
            'quotes': [
                {
                    'symbol': f'TEST{i}',
                    'regularMarketPrice': 100.0 + i,
                    'regularMarketChange': 1.0,
                    'regularMarketChangePercent': 1.0
                }
                for i in range(20)
            ]
        }
        
        mock_yf.screen.return_value = many_quotes
        
        fetcher = StocksFetcher()
        result = await fetcher.fetch_screener(ScreenerType.GAINERS, limit=5)
        
        # Should only return up to 5 results
        assert len(result) <= 5
    
    @patch('core.data.stocks_data._YFINANCE_AVAILABLE', True)
    @patch('core.data.stocks_data.yf')
    async def test_multiple_symbols(self, mock_yf):
        """Test fetching multiple stock symbols."""
        def mock_ticker_factory(symbol):
            mock = MagicMock()
            mock.info = {
                'symbol': symbol,
                'regularMarketPrice': 100.0,
                'regularMarketChange': 1.0,
                'regularMarketChangePercent': 1.0
            }
            return mock
        
        mock_yf.Ticker.side_effect = lambda s: mock_ticker_factory(s)
        
        fetcher = StocksFetcher(symbols=['AAPL', 'GOOGL', 'MSFT'])
        result = await fetcher.fetch_quotes(['AAPL', 'GOOGL', 'MSFT'])
        
        assert len(result) >= 1  # At least some should succeed
    
    @patch('core.data.stocks_data._YFINANCE_AVAILABLE', False)
    async def test_fetch_quotes_when_yfinance_unavailable(self):
        """Test that fetcher handles yfinance being unavailable gracefully."""
        fetcher = StocksFetcher(symbols=['AAPL'])
        result = await fetcher.fetch_quotes(['AAPL'])
        
        # Should return empty list when yfinance is unavailable
        assert result == []
    
    @patch('core.data.stocks_data._YFINANCE_AVAILABLE', False)
    async def test_fetch_screener_when_yfinance_unavailable(self):
        """Test that screener handles yfinance being unavailable gracefully."""
        fetcher = StocksFetcher()
        result = await fetcher.fetch_screener(ScreenerType.GAINERS, limit=5)
        
        # Should return empty list when yfinance is unavailable
        assert result == []
