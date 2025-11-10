"""
Data fetching modules for LED panel display system.

This package contains modules for fetching data from various sources:
- Sports scores and game information
- Weather data and forecasts
- Stock market data and quotes
"""
import os

# Define constants that can be imported without triggering module dependencies
CITY = os.getenv("WEATHER_CITY", "Detroit,US")  # Format: "City,CountryCode"
STOCKS_SYMBOLS = [s.strip() for s in os.getenv("STOCKS_SYMBOLS", "AAPL,GOOGL,MSFT,TSLA").split(",") if s.strip()]
STOCKS_CHECK_INTERVAL = int(os.getenv("STOCKS_CHECK_INTERVAL", "300"))

# Lazy imports to avoid dependency issues during import
def __getattr__(name):
    if name in ('fetch_all_games', 'get_league_letter'):
        from .sports_data import fetch_all_games, get_league_letter
        return locals()[name]
    elif name in ('fetch_current_weather', 'fetch_hourly_forecast', 'fetch_daily_forecast', 'WEATHER_API_KEY'):
        from .weather_data import (
            fetch_current_weather, fetch_hourly_forecast, fetch_daily_forecast,
            WEATHER_API_KEY
        )
        return locals()[name]
    elif name == 'fetch_stock_quotes':
        from .stocks_data import fetch_stock_quotes
        return fetch_stock_quotes
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    # Sports data
    'fetch_all_games', 'get_league_letter',
    # Weather data
    'fetch_current_weather', 'fetch_hourly_forecast', 'fetch_daily_forecast',
    'CITY', 'WEATHER_API_KEY',
    # Stocks data
    'fetch_stock_quotes', 'STOCKS_SYMBOLS', 'STOCKS_CHECK_INTERVAL'
]
