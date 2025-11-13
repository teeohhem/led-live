"""
Weather mode - displays full weather information.
"""
from datetime import datetime
from typing import Optional
from PIL import Image
import logging

from .base_mode import BaseMode
from core.data import fetch_current_weather, fetch_hourly_forecast, fetch_daily_forecast
from core.rendering import render_weather

logger = logging.getLogger(__name__)


class WeatherMode(BaseMode):
    """Full weather display mode."""
    
    def __init__(self, config):
        super().__init__("weather", config)
        self.current_weather = None
        self.forecasts = None
        self.prev_weather = None
        self.prev_forecasts = None
        
        # Config
        self.check_interval = config.get('WEATHER_CHECK_INTERVAL', 300)
        self.refresh_interval = config.get('DISPLAY_WEATHER_REFRESH_INTERVAL', 2)
        self.forecast_mode = config.get('WEATHER_FORECAST_MODE', 'daily')
    
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
        """Check if weather data is available."""
        return self.current_weather is not None
    
    def should_fetch(self, now: datetime) -> bool:
        """Check if data needs updating."""
        if self.last_fetch is None:
            return True
        return (now - self.last_fetch).total_seconds() >= self.check_interval
    
    def should_render(self, now: datetime) -> bool:
        """Check if re-render is needed."""
        # Data changed?
        data_changed = (
            self.current_weather != self.prev_weather or
            self.forecasts != self.prev_forecasts
        )
        
        # Periodic refresh needed?
        needs_refresh = (
            self.last_render is None or
            (now - self.last_render).total_seconds() >= self.refresh_interval
        )
        
        if data_changed:
            self.prev_weather = self.current_weather.copy() if self.current_weather else None
            self.prev_forecasts = self.forecasts.copy() if self.forecasts else None
            return True
        
        return needs_refresh
    
    async def render(self, width: int, height: int) -> Optional[Image.Image]:
        """Render weather display."""
        return render_weather(
            self.current_weather,
            self.forecasts,
            width=width,
            height=height
        )
    
    def has_priority(self) -> bool:
        """Weather never has priority."""
        return False

