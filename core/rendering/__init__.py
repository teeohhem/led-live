"""
Rendering modules for LED panel display system.

This package contains modules for rendering different types of content
as PIL Images for display on LED panels:
- Sports scoreboards with team logos
- Weather displays with icons and forecasts
- Themed clock displays
- Stock market tickers
"""

# Lazy imports to avoid dependency issues during import
def __getattr__(name):
    if name in ('render_scoreboard', 'render_upcoming_games'):
        from .sports_display_png import render_scoreboard, render_upcoming_games
        return locals()[name]
    elif name in ('render_weather', 'render_weather_bottom_panel'):
        from .weather_display_png import render_weather, render_weather_bottom_panel
        return locals()[name]
    elif name == 'render_clock_with_weather_split':
        from .clock_display_png import render_clock_with_weather_split
        return render_clock_with_weather_split
    elif name == 'render_stocks':
        from .stocks_display_png import render_stocks
        return render_stocks
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    # Sports rendering
    'render_scoreboard', 'render_upcoming_games',
    # Weather rendering
    'render_weather', 'render_weather_bottom_panel',
    # Clock rendering
    'render_clock_with_weather_split',
    # Stocks rendering
    'render_stocks'
]
