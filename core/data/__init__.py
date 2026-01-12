"""
Data fetching modules for sports, stocks, and weather.

All fetchers use a common base class with automatic retry logic,
caching, and consistent error handling.
"""

# Export fetcher classes for direct use
from .base_fetcher import DataFetcher
from .weather_data import WeatherFetcher, weather_fetcher
from .sports_data import SportsFetcher, sports_fetcher, GameState, League
from .stocks_data import StocksFetcher, stocks_fetcher, ScreenerType

# Export module-level fetcher instances (convenient singletons)
__all__ = [
    # Base class
    'DataFetcher',
    
    # Fetcher classes
    'WeatherFetcher',
    'SportsFetcher', 
    'StocksFetcher',
    
    # Module-level instances (singletons)
    'weather_fetcher',
    'sports_fetcher',
    'stocks_fetcher',
    
    # Enums
    'GameState',
    'League',
    'ScreenerType',
]
