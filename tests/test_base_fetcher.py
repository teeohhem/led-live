"""
Unit tests for DataFetcher base class.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import httpx

from core.data.base_fetcher import DataFetcher


# Concrete implementation for testing
class DummyFetcher(DataFetcher[dict]):
    """Dummy implementation of DataFetcher for testing."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fetch_called = False
        self.fetch_return_value = {'test': 'data'}
    
    async def fetch(self):
        """Test implementation of abstract fetch method."""
        self.fetch_called = True
        return self.fetch_return_value


@pytest.mark.asyncio
class TestDataFetcher:
    """Test cases for DataFetcher."""
    
    async def test_initialization(self):
        """Test fetcher initialization with default parameters."""
        fetcher = DummyFetcher()
        
        assert fetcher._cache_ttl == 60
        assert fetcher._timeout == 10.0
        assert fetcher._cache is None
        assert fetcher._cache_timestamp is None
        assert fetcher._client is None
    
    async def test_initialization_with_custom_params(self):
        """Test fetcher initialization with custom parameters."""
        fetcher = DummyFetcher(
            cache_ttl=600,
            timeout=30.0
        )
        
        assert fetcher._cache_ttl == 600
        assert fetcher._timeout == 30.0
    
    async def test_context_manager(self):
        """Test fetcher as context manager."""
        async with DummyFetcher() as fetcher:
            assert fetcher._client is not None
            assert isinstance(fetcher._client, httpx.AsyncClient)
        
        # Client should be closed after context exit
        assert fetcher._client is None
    
    async def test_cache_miss_fetches_fresh_data(self):
        """Test that cache miss triggers fresh data fetch."""
        fetcher = DummyFetcher()
        
        result = await fetcher.get_cached_or_fetch()
        
        assert fetcher.fetch_called
        assert result == {'test': 'data'}
        assert fetcher._cache == {'test': 'data'}
        assert fetcher._cache_timestamp is not None
    
    async def test_cache_hit_returns_cached_data(self):
        """Test that valid cache returns cached data without fetching."""
        fetcher = DummyFetcher()
        
        # First fetch to populate cache
        await fetcher.get_cached_or_fetch()
        fetcher.fetch_called = False  # Reset flag
        
        # Second fetch should use cache
        result = await fetcher.get_cached_or_fetch()
        
        assert not fetcher.fetch_called  # Should not fetch again
        assert result == {'test': 'data'}
    
    async def test_cache_expiry_refetches_data(self):
        """Test that expired cache triggers fresh data fetch."""
        fetcher = DummyFetcher(cache_ttl=1)  # 1 second TTL
        
        # First fetch
        await fetcher.get_cached_or_fetch()
        
        # Wait for cache to expire
        await asyncio.sleep(1.1)
        
        fetcher.fetch_called = False
        fetcher.fetch_return_value = {'test': 'new_data'}
        
        # Should fetch fresh data
        result = await fetcher.get_cached_or_fetch()
        
        assert fetcher.fetch_called
        assert result == {'test': 'new_data'}
    
    async def test_force_refresh(self):
        """Test force_refresh bypasses cache."""
        fetcher = DummyFetcher()
        
        # First fetch
        await fetcher.get_cached_or_fetch()
        
        fetcher.fetch_called = False
        fetcher.fetch_return_value = {'test': 'forced_data'}
        
        # Force refresh
        result = await fetcher.get_cached_or_fetch(force_refresh=True)
        
        assert fetcher.fetch_called
        assert result == {'test': 'forced_data'}
    
    async def test_is_cache_valid(self):
        """Test cache validation logic."""
        fetcher = DummyFetcher()
        
        # No cache
        assert not fetcher._is_cache_valid()
        
        # Populate cache
        await fetcher.get_cached_or_fetch()
        
        # Cache should be valid
        assert fetcher._is_cache_valid()
    
    async def test_clear_cache(self):
        """Test cache clearing."""
        fetcher = DummyFetcher()
        
        # Populate cache
        await fetcher.get_cached_or_fetch()
        assert fetcher._cache is not None
        
        # Clear cache
        fetcher.clear_cache()
        assert fetcher._cache is None
        assert fetcher._cache_timestamp is None
    
    async def test_cache_age_property(self):
        """Test cache_age property."""
        fetcher = DummyFetcher()
        
        # No cache
        assert fetcher.cache_age is None
        
        # Populate cache
        await fetcher.get_cached_or_fetch()
        
        # Cache age should be close to 0
        age = fetcher.cache_age
        assert age is not None
        assert age < 1.0  # Less than 1 second old
    
    async def test_has_cache_property(self):
        """Test has_cache property."""
        fetcher = DummyFetcher()
        
        # No cache
        assert not fetcher.has_cache
        
        # Populate cache
        await fetcher.get_cached_or_fetch()
        
        # Has cache
        assert fetcher.has_cache
    
    @patch('core.data.base_fetcher.httpx.AsyncClient')
    async def test_fetch_with_retry_success(self, mock_client_class):
        """Test successful HTTP request."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'success': True}
        mock_response.raise_for_status = MagicMock()
        mock_response.status_code = 200
        
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        mock_client_class.return_value = mock_client
        
        async with DummyFetcher() as fetcher:
            result = await fetcher.fetch_with_retry('http://example.com/api')
        
        assert result == {'success': True}
    
    @patch('core.data.base_fetcher.httpx.AsyncClient')
    @patch('core.data.base_fetcher.asyncio.sleep')
    async def test_fetch_with_retry_retries_on_failure(self, mock_sleep, mock_client_class):
        """Test retry logic on HTTP errors."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError(
                "Server Error",
                request=MagicMock(),
                response=mock_response
            )
        )
        
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        mock_client_class.return_value = mock_client
        
        async with DummyFetcher() as fetcher:
            result = await fetcher.fetch_with_retry('http://example.com/api', max_retries=3)
        
        assert result is None
        assert mock_client.get.call_count == 3
    
    async def test_none_data_does_not_update_cache(self):
        """Test that None return value doesn't update cache."""
        fetcher = DummyFetcher()
        fetcher.fetch_return_value = None
        
        result = await fetcher.get_cached_or_fetch()
        
        assert result is None
        assert fetcher._cache is None
        assert fetcher._cache_timestamp is None
    
    async def test_fetch_is_abstract(self):
        """Test that DataFetcher cannot be instantiated directly."""
        with pytest.raises(TypeError):
            # This should fail because fetch is abstract
            DataFetcher()
