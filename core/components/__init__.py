"""
Component-based rendering system for LED panels.

Components are self-contained widgets that can be composed into templates.
Each component knows how to fetch its data and render itself.
"""

from .base import Component, ComponentRegistry
from .clock_component import ClockComponent
from .weather_components import WeatherCurrentComponent, WeatherExtendedComponent
from .sports_component import SportsLiveComponent
from .stocks_component import StocksComponent

# Register all components
registry = ComponentRegistry()
registry.register('clock', ClockComponent)
registry.register('weather_current', WeatherCurrentComponent)
registry.register('weather_extended', WeatherExtendedComponent)
registry.register('sports_live', SportsLiveComponent)
registry.register('stocks', StocksComponent)

__all__ = [
    'Component',
    'ComponentRegistry',
    'registry',
    'ClockComponent',
    'WeatherCurrentComponent',
    'WeatherExtendedComponent',
    'SportsLiveComponent',
    'StocksComponent',
]


