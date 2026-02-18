"""
Base class for all data fetchers with common patterns.

Provides:
- Automatic retry logic with exponential backoff
- Built-in caching with configurable TTL
- Consistent error handling
- Connection pooling via async context manager
- Type-safe interfaces
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, TypeVar, Generic
import httpx

T = TypeVar('T')

logger = logging.getLogger(__name__)


class DataFetcher(ABC, Generic[T]):
    """
    Base class for data fetchers with caching and retry logic.
    
    Usage:
        class MyFetcher(DataFetcher[List[Dict]]):
            async def fetch(self) -> Optional[List[Dict]]:
                data = await self.fetch_with_retry("https://api.example.com/data")
                return self._parse(data)
        
        # With context manager (recommended)
        async with MyFetcher(cache_ttl=60) as fetcher:
            data = await fetcher.get_cached_or_fetch()
        
        # Or manually
        fetcher = MyFetcher(cache_ttl=60)
        data = await fetcher.get_cached_or_fetch()
    """
    
    def __init__(
        self, 
        cache_ttl: int = 60,
        timeout: float = 10.0,
        logger_name: Optional[str] = None
    ):
        """
        Initialize data fetcher.
        
        Args:
            cache_ttl: Cache time-to-live in seconds
            timeout: HTTP request timeout in seconds
            logger_name: Custom logger name (defaults to class name)
        """
        self.logger = logging.getLogger(logger_name or self.__class__.__name__)
        self._cache: Optional[T] = None
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl = cache_ttl
        self._client: Optional[httpx.AsyncClient] = None
        self._timeout = timeout
    
    async def __aenter__(self):
        """Async context manager entry - creates HTTP client."""
        self._client = httpx.AsyncClient(timeout=self._timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - closes HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    def _is_cache_valid(self) -> bool:
        """
        Check if cache is still valid.
        
        Returns:
            True if cache exists and hasn't expired
        """
        if self._cache is None or self._cache_timestamp is None:
            return False
        
        age = (datetime.now() - self._cache_timestamp).total_seconds()
        is_valid = age < self._cache_ttl
        
        if not is_valid:
            self.logger.debug(f"Cache expired ({age:.1f}s > {self._cache_ttl}s)")
        
        return is_valid
    
    def clear_cache(self) -> None:
        """Clear cached data."""
        self._cache = None
        self._cache_timestamp = None
        self.logger.debug("Cache cleared")
    
    async def fetch_with_retry(
        self, 
        url: str, 
        max_retries: int = 3,
        backoff_factor: float = 1.5,
        params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch data with exponential backoff retry.
        
        Args:
            url: URL to fetch
            max_retries: Maximum number of retry attempts
            backoff_factor: Multiplier for wait time between retries
            params: Optional query parameters
            
        Returns:
            JSON response or None if all retries failed
        """
        # Ensure we have a client
        if not self._client:
            self._client = httpx.AsyncClient(timeout=self._timeout)
        
        for attempt in range(max_retries):
            try:
                self.logger.debug(f"Fetching {url} (attempt {attempt+1}/{max_retries})")
                
                resp = await self._client.get(url, params=params)
                
                if resp.status_code == 200:
                    self.logger.debug(f"Successfully fetched from {url}")
                    return resp.json()
                
                self.logger.warning(
                    f"HTTP {resp.status_code} on attempt {attempt+1}/{max_retries} for {url}"
                )
                
            except httpx.TimeoutException:
                self.logger.warning(
                    f"Timeout on attempt {attempt+1}/{max_retries} for {url}"
                )
            except httpx.HTTPError as e:
                self.logger.warning(
                    f"HTTP error on attempt {attempt+1}/{max_retries}: {e}"
                )
            except Exception as e:
                self.logger.warning(
                    f"Error on attempt {attempt+1}/{max_retries}: {e}"
                )
            
            # Wait before retry (exponential backoff)
            if attempt < max_retries - 1:
                wait_time = backoff_factor ** attempt
                self.logger.debug(f"Waiting {wait_time:.1f}s before retry...")
                await asyncio.sleep(wait_time)
        
        self.logger.error(f"All {max_retries} attempts failed for {url}")
        return None
    
    async def get_cached_or_fetch(self, force_refresh: bool = False) -> Optional[T]:
        """
        Get data from cache or fetch fresh data.
        
        Args:
            force_refresh: Bypass cache and fetch fresh data
            
        Returns:
            Cached or freshly fetched data, or None on error
        """
        if not force_refresh and self._is_cache_valid():
            age = (datetime.now() - self._cache_timestamp).total_seconds()
            self.logger.debug(f"Using cached data ({age:.1f}s old)")
            return self._cache
        
        self.logger.debug("Fetching fresh data...")
        data = await self.fetch()
        
        if data is not None:
            self._cache = data
            self._cache_timestamp = datetime.now()
            self.logger.debug("Data fetched and cached successfully")
        else:
            self.logger.warning("Failed to fetch data")
        
        return data
    
    @abstractmethod
    async def fetch(self) -> Optional[T]:
        """
        Fetch data from source. Must be implemented by subclasses.
        
        Returns:
            Fetched data or None on error
        """
        pass
    
    @property
    def cache_age(self) -> Optional[float]:
        """
        Get age of cached data in seconds.
        
        Returns:
            Age in seconds, or None if no cache
        """
        if self._cache_timestamp is None:
            return None
        return (datetime.now() - self._cache_timestamp).total_seconds()
    
    @property
    def has_cache(self) -> bool:
        """Check if cache exists (regardless of validity)."""
        return self._cache is not None


