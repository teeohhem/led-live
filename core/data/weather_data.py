"""
Weather data fetching from OpenWeatherMap API.

Refactored to use base fetcher class for:
- Automatic retry logic
- Built-in caching
- Consistent error handling
- Better testability
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from collections import defaultdict
from PIL import Image

from .base_fetcher import DataFetcher

logger = logging.getLogger(__name__)

# Import configuration (loaded at startup via config.py)
from config import WEATHER_API_KEY, WEATHER_ZIPCODE as ZIPCODE, WEATHER_UNITS as UNITS

# Alias for backward compatibility
OPENWEATHER_API_KEY = WEATHER_API_KEY

# API URLs
BASE_URL = "https://api.openweathermap.org/data/2.5"
GEO_URL = "http://api.openweathermap.org/geo/1.0"

# ============================================================================
# Color and Icon Configuration
# ============================================================================

WEATHER_COLORS = {
    "clear": (255, 255, 0),      # Yellow for sunny
    "clouds": (180, 180, 180),   # Gray for cloudy
    "rain": (0, 100, 255),       # Blue for rain
    "drizzle": (100, 150, 255),  # Light blue for drizzle
    "thunderstorm": (255, 0, 255), # Purple for storms
    "snow": (255, 255, 255),     # White for snow
    "mist": (150, 150, 150),     # Gray for mist/fog
    "default": (0, 255, 0)       # Green default
}

WEATHER_ICONS = {
    "clear": "./logos/weather/sun.png",
    "clouds": "./logos/weather/clouds.png",
    "rain": "./logos/weather/rain.png",
    "drizzle": "./logos/weather/rain.png",
    "thunderstorm": "./logos/weather/thunderstorm.png",
    "snow": "./logos/weather/snow.png",
    "mist": "./logos/weather/clouds.png",
    "default": "./logos/weather/sun.png"
}


def load_weather_icon(condition: str, size: Tuple[int, int] = (12, 12)) -> Optional[Image.Image]:
    """
    Load and resize weather icon for given condition.
    
    Args:
        condition: Weather condition name
        size: Desired icon size (width, height)
        
    Returns:
        Resized PIL Image or None if not found
    """
    icon_path = WEATHER_ICONS.get(condition, WEATHER_ICONS["default"])
    try:
        icon = Image.open(icon_path).convert("RGBA")
        icon = icon.resize(size, Image.Resampling.LANCZOS)
        return icon
    except FileNotFoundError:
        logger.warning(f"Icon not found: {icon_path}")
        return None


def get_icon_pixels(
    icon: Optional[Image.Image], 
    offset: Tuple[int, int] = (0, 0)
) -> List[Tuple[int, int, int, int, int]]:
    """
    Convert icon to list of pixel coordinates with colors.
    
    Args:
        icon: PIL Image (RGBA mode)
        offset: Offset to apply to coordinates
        
    Returns:
        List of (x, y, r, g, b) tuples for non-transparent pixels
    """
    if icon is None:
        return []
    
    pixels = []
    for y in range(icon.height):
        for x in range(icon.width):
            r, g, b, a = icon.getpixel((x, y))
            if a > 128:  # Only draw non-transparent pixels
                pixels.append((offset[0] + x, offset[1] + y, r, g, b))
    return pixels


# ============================================================================
# Weather Data Fetcher
# ============================================================================

class WeatherFetcher(DataFetcher[Dict[str, Any]]):
    """
    Fetcher for OpenWeatherMap data with caching and retry logic.
    
    Handles:
    - Current weather conditions
    - Hourly forecast (next 4 hours)
    - Daily forecast (next 2 days)
    - Geocoding (zipcode to lat/lon)
    """
    
    def __init__(
        self, 
        api_key: str, 
        zipcode: str, 
        units: str = "imperial",
        cache_ttl: int = 300  # 5 minutes default cache
    ):
        """
        Initialize weather fetcher.
        
        Args:
            api_key: OpenWeatherMap API key
            zipcode: Zipcode for location
            units: Units system ("imperial" or "metric")
            cache_ttl: Cache time-to-live in seconds
        """
        super().__init__(cache_ttl=cache_ttl, logger_name='weather_fetcher')
        self.api_key = api_key
        self.zipcode = zipcode
        self.units = units
        
        # Cache coordinates separately (rarely change)
        self._lat: Optional[float] = None
        self._lon: Optional[float] = None
    
    async def _get_coordinates(self) -> Tuple[float, float]:
        """
        Get latitude/longitude from zipcode (cached).
        
        Returns:
            Tuple of (latitude, longitude)
            
        Raises:
            ValueError: If zipcode cannot be geocoded
        """
        if self._lat is not None and self._lon is not None:
            self.logger.debug(f"Using cached coordinates for zipcode: {self.zipcode}")
            return self._lat, self._lon
        
        url = f"{GEO_URL}/zip"
        params = {
            "zip": self.zipcode,
            "appid": self.api_key
        }
        
        self.logger.info(f"Getting coordinates for zipcode: {self.zipcode}")
        data = await self.fetch_with_retry(url, params=params)
        
        if data:
            self._lat = data["lat"]
            self._lon = data["lon"]
            self.logger.info(f"Coordinates: {self._lat}, {self._lon}")
            return self._lat, self._lon
        
        raise ValueError(f"Could not geocode zipcode: {self.zipcode}")
    
    async def fetch(self) -> Optional[Dict[str, Any]]:
        """
        Fetch current weather (implements abstract method).
        
        Returns:
            Weather data dict or None on error
        """
        return await self.fetch_current()
    
    async def fetch_current(self) -> Optional[Dict[str, Any]]:
        """
        Fetch current weather conditions.
        
        Returns:
            Dict with current weather data
        """
        try:
            lat, lon = await self._get_coordinates()
        except ValueError as e:
            self.logger.error(str(e))
            return None
        
        url = f"{BASE_URL}/weather"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.api_key,
            "units": self.units
        }
        
        data = await self.fetch_with_retry(url, params=params)
        
        if data:
            weather = self._parse_current_weather(data)
            self.logger.info(f"☀️ Weather: {weather['temp']}°F, {weather['description']}")
            return weather
        
        return None
    
    @staticmethod
    def _parse_current_weather(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse OpenWeatherMap current weather response.
        
        Args:
            data: Raw API response
            
        Returns:
            Parsed weather dict
        """
        return {
            "temp": round(data["main"]["temp"]),
            "feels_like": round(data["main"]["feels_like"]),
            "temp_min": round(data["main"]["temp_min"]),
            "temp_max": round(data["main"]["temp_max"]),
            "humidity": data["main"]["humidity"],
            "description": data["weather"][0]["description"].title(),
            "condition": data["weather"][0]["main"].lower(),
            "wind_speed": round(data["wind"]["speed"]),
            "city": data["name"]
        }
    
    async def fetch_hourly(self, hours: int = 4) -> List[Dict[str, Any]]:
        """
        Fetch hourly forecast.
        
        Args:
            hours: Number of hours to fetch (max ~40)
            
        Returns:
            List of hourly forecast dicts
        """
        try:
            lat, lon = await self._get_coordinates()
        except ValueError as e:
            self.logger.error(str(e))
            return []
        
        url = f"{BASE_URL}/forecast"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.api_key,
            "units": self.units,
            "cnt": hours
        }
        
        data = await self.fetch_with_retry(url, params=params)
        
        if not data:
            return []
        
        forecasts = []
        for item in data.get("list", []):
            time = datetime.fromtimestamp(item["dt"]).strftime("%I%p").lstrip("0")
            forecasts.append({
                "time": time,
                "temp": round(item["main"]["temp"]),
                "condition": item["weather"][0]["main"].lower(),
                "description": item["weather"][0]["description"]
            })
        
        self.logger.info(f"📅 Fetched {len(forecasts)} hourly forecasts")
        return forecasts
    
    async def fetch_daily(self, days: int = 2) -> List[Dict[str, Any]]:
        """
        Fetch daily forecast (next N days).
        
        Args:
            days: Number of days to fetch
            
        Returns:
            List of daily forecast dicts with high temp and most common condition
        """
        try:
            lat, lon = await self._get_coordinates()
        except ValueError as e:
            self.logger.error(str(e))
            return []
        
        url = f"{BASE_URL}/forecast"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.api_key,
            "units": self.units
        }
        
        data = await self.fetch_with_retry(url, params=params)
        
        if not data:
            return []
        
        # Group forecasts by day
        daily_data = defaultdict(lambda: {"temps": [], "conditions": []})
        
        for item in data.get("list", []):
            dt = datetime.fromtimestamp(item["dt"])
            day_key = dt.strftime("%a")  # "Mon", "Tue", etc.
            
            daily_data[day_key]["temps"].append(item["main"]["temp"])
            daily_data[day_key]["conditions"].append(item["weather"][0]["main"].lower())
        
        # Create daily forecasts (skip today, get next N days)
        today = datetime.now().strftime("%a")
        forecasts = []
        
        for day_key, day_info in list(daily_data.items())[1:days+1]:
            if day_key == today:
                continue
            
            # Get high temp for the day
            high_temp = round(max(day_info["temps"]))
            
            # Most common condition
            condition = max(set(day_info["conditions"]), key=day_info["conditions"].count)
            
            forecasts.append({
                "time": day_key,  # Day name
                "temp": high_temp,
                "condition": condition,
                "description": condition.title()
            })
        
        self.logger.info(f"📅 Fetched {len(forecasts)} daily forecasts")
        return forecasts[:days]


# ============================================================================
# Module-level API - use WeatherFetcher class directly
# ============================================================================

# For convenience, create module-level fetcher instance
weather_fetcher = WeatherFetcher(
    api_key=WEATHER_API_KEY,
    zipcode=ZIPCODE,
    units=UNITS,
    cache_ttl=300
)
