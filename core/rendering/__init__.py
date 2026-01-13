"""
Rendering modules for LED panel display system.

Template-based rendering system for LED panels.
All content is rendered using layout templates from core/layout/templates/
"""

# Template-based renderers (primary)
from .templated_renderer import (
    TemplatedSportsRenderer,
    TemplatedStocksRenderer,
    TemplatedWeatherRenderer,
)

# Clock rendering
from .clock_display_png import render_clock_with_weather_split

__all__ = [
    # Template-based renderers (recommended)
    'TemplatedSportsRenderer',
    'TemplatedStocksRenderer',
    'TemplatedWeatherRenderer',
    # Clock rendering
    'render_clock_with_weather_split',
]
