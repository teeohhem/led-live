"""
Weather components for displaying weather data.
"""

from typing import Optional, Any, Dict, List
from PIL import Image
from .base import Component


class WeatherCurrentComponent(Component):
    """
    Displays current weather with icon, temp, and condition.
    
    Config options:
        - zipcode: Override default zipcode
        - show_icon: Show weather icon (default: true)
        - show_feels_like: Show feels-like temp (default: false)
    """
    
    async def fetch_data(self) -> Optional[Dict[str, Any]]:
        """Fetch current weather data."""
        from core.data import weather_fetcher
        
        try:
            data = await weather_fetcher.get_cached_or_fetch()
            return data
        except Exception as e:
            self.logger.error(f"Failed to fetch weather: {e}")
            return None
    
    def render(self, data: Optional[Dict[str, Any]] = None) -> Image.Image:
        """
        Render current weather.
        
        Args:
            data: Current weather dict from fetch_data()
        
        Returns:
            PIL Image
        """
        from core.rendering.templated_renderer import TemplatedWeatherRenderer
        from core.layout.loader import LayoutLoader
        from config import get_all_config
        
        # Load weather template for this size
        config_dict = get_all_config()
        loader = LayoutLoader(config_dict)
        
        # Get template matching our dimensions
        layout = loader.get_layout_for_dimensions(self.width, self.height)
        renderer = TemplatedWeatherRenderer(layout)
        
        return renderer.render_weather(data or {}, mode='current')


class WeatherExtendedComponent(Component):
    """
    Displays multi-day forecast with icons and high/low temps.
    
    Config options:
        - days: Number of days to show (default: 4)
        - zipcode: Override default zipcode
    """
    
    async def fetch_data(self) -> Optional[List[Dict[str, Any]]]:
        """Fetch forecast data."""
        from core.data import weather_fetcher
        
        try:
            # Fetch daily forecast
            forecasts = await weather_fetcher.fetch_daily()
            
            # Limit to requested number of days
            days = self.config.get('days', 4)
            return forecasts[:days] if forecasts else None
        except Exception as e:
            self.logger.error(f"Failed to fetch forecast: {e}")
            return None
    
    def render(self, data: Optional[List[Dict[str, Any]]] = None) -> Image.Image:
        """
        Render extended forecast.
        
        Args:
            data: List of forecast dicts from fetch_data()
        
        Returns:
            PIL Image
        """
        from core.rendering.templated_renderer import TemplatedWeatherRenderer
        from core.layout.loader import LayoutLoader
        from config import get_all_config
        
        # Load weather template for this size
        config_dict = get_all_config()
        loader = LayoutLoader(config_dict)
        
        # Get template matching our dimensions
        layout = loader.get_layout_for_dimensions(self.width, self.height)
        renderer = TemplatedWeatherRenderer(layout)
        
        return renderer.render_forecast_extended(data or [])


