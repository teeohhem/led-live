"""
Display mode abstractions for the LED panel system.

Each mode is responsible for its own data fetching, rendering, and state management.
"""
from .base_mode import BaseMode, ModeResult
from .sports_mode import SportsMode
from .clock_mode import ClockMode
from .weather_mode import WeatherMode
from .stocks_mode import StocksMode
from .ticker_mode import TickerMode

__all__ = [
    'BaseMode',
    'ModeResult',
    'SportsMode',
    'ClockMode',
    'WeatherMode',
    'StocksMode',
    'TickerMode',
]

