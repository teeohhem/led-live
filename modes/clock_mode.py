"""
Clock mode - displays themed clock with weather.
"""
from datetime import datetime
from typing import Optional
from PIL import Image
import logging

from .base_mode import BaseMode
from core.data import fetch_current_weather, fetch_hourly_forecast, fetch_daily_forecast
from core.rendering import render_clock_with_weather_split

logger = logging.getLogger(__name__)


class ClockMode(BaseMode):
    """Clock + Weather display mode."""
    
    def __init__(self, config):
        super().__init__("clock", config)
        self.current_weather = None
        self.forecasts = None
        
        # Config
        self.weather_check_interval = config.get('WEATHER_CHECK_INTERVAL', 300)
        self.refresh_interval = config.get('DISPLAY_CLOCK_REFRESH_INTERVAL', 60)
        self.forecast_mode = config.get('WEATHER_FORECAST_MODE', 'daily')
        self.theme = config.get('CLOCK_THEME', 'stranger_things')
        self.hour24 = config.get('CLOCK_24H', False)
    
    async def fetch_data(self) -> bool:
        """Fetch weather data."""
        try:
            self.current_weather = await fetch_current_weather()
            if self.forecast_mode == 'daily':
                self.forecasts = await fetch_daily_forecast()
            else:
                self.forecasts = await fetch_hourly_forecast()
            
            self.last_fetch = datetime.now()
            return True
        except Exception as e:
            logger.error(f"Error fetching weather: {e}")
            return False
    
    def has_data(self) -> bool:
        """Clock always has data (time)."""
        return self.current_weather is not None
    
    def should_fetch(self, now: datetime) -> bool:
        """Check if weather data needs updating."""
        if self.last_fetch is None:
            return True
        return (now - self.last_fetch).total_seconds() >= self.weather_check_interval
    
    def should_render(self, now: datetime) -> bool:
        """Re-render every minute or on refresh interval."""
        if self.last_render is None:
            return True
        return (now - self.last_render).total_seconds() >= self.refresh_interval
    
    async def render(self, width: int, height: int) -> Optional[Image.Image]:
        """Render clock + weather."""
        return render_clock_with_weather_split(
            self.current_weather,
            self.forecasts,
            total_width=width,
            total_height=height,
            theme=self.theme,
            hour24=self.hour24
        )
    
    def has_priority(self) -> bool:
        """Clock never has priority."""
        return False

