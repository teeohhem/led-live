"""
Rendering modules for LED panel display system.

Template-based rendering system for LED panels.
All content is rendered using layout templates from core/layout/templates/

Legacy rendering functions have been moved to legacy/ directory.
"""

# Template-based renderers (primary)
from .templated_renderer import (
    TemplatedSportsRenderer,
    TemplatedStocksRenderer,
    TemplatedWeatherRenderer,
)

# Legacy imports (deprecated - for backward compatibility only)
def __getattr__(name):
    import warnings
    import sys
    
    # Deprecated legacy renderers - point to legacy folder
    if name in ('render_scoreboard', 'render_upcoming_games'):
        warnings.warn(
            f"'{name}' is deprecated. Use TemplatedSportsRenderer with layout templates. "
            "See core/layout/templates/ for template files.",
            DeprecationWarning,
            stacklevel=2
        )
        from legacy.sports_display_png import render_scoreboard, render_upcoming_games
        return locals()[name]
    elif name in ('render_weather', 'render_weather_bottom_panel'):
        warnings.warn(
            f"'{name}' is deprecated. Weather templates available in core/layout/templates/",
            DeprecationWarning,
            stacklevel=2
        )
        from legacy.weather_display_png import render_weather, render_weather_bottom_panel
        return locals()[name]
    elif name == 'render_stocks':
        warnings.warn(
            "'render_stocks' is deprecated. Use TemplatedStocksRenderer with layout templates. "
            "See core/layout/templates/ for template files.",
            DeprecationWarning,
            stacklevel=2
        )
        from legacy.stocks_display_png import render_stocks
        return render_stocks
    elif name == 'render_clock_with_weather_split':
        from .clock_display_png import render_clock_with_weather_split
        return render_clock_with_weather_split
    
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    # Template-based renderers (recommended)
    'TemplatedSportsRenderer',
    'TemplatedStocksRenderer',
    'TemplatedWeatherRenderer',
    
    # Legacy (deprecated - backward compatibility only)
    'render_scoreboard',
    'render_upcoming_games',
    'render_weather',
    'render_stocks',
    'render_clock_with_weather_split',
]
