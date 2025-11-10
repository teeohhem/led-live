"""
Weather data fetching from OpenWeatherMap API
"""
import httpx
import os
from datetime import datetime
from pathlib import Path
from PIL import Image

# Load environment variables from config.env if it exists
config_file = Path(__file__).parent / "config.env"
if config_file.exists():
    with open(config_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip())

# --- Settings ---
# Get your free API key from: https://openweathermap.org/api
OPENWEATHER_API_KEY = os.getenv(
    "OPENWEATHER_API_KEY",
    "your-api-key-here"  # Replace or set in config.env
)
WEATHER_API_KEY = OPENWEATHER_API_KEY  # Alias for backward compatibility
CITY = os.getenv("WEATHER_CITY", "Detroit,US")  # Format: "City,CountryCode"
UNITS = os.getenv("WEATHER_UNITS", "imperial")  # imperial = Fahrenheit, metric = Celsius

# --- Weather condition colors ---
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

# --- Weather condition icons ---
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


def load_weather_icon(condition, size=(12, 12)):
    """Load and resize weather icon for given condition"""
    icon_path = WEATHER_ICONS.get(condition, WEATHER_ICONS["default"])
    try:
        icon = Image.open(icon_path).convert("RGBA")
        icon = icon.resize(size, Image.Resampling.LANCZOS)
        return icon
    except FileNotFoundError:
        print(f"⚠️ Icon not found: {icon_path}")
        return None


def get_icon_pixels(icon, offset=(0, 0)):
    """Convert icon to list of (x, y, r, g, b) tuples for non-transparent pixels"""
    if icon is None:
        return []
    
    pixels = []
    for y in range(icon.height):
        for x in range(icon.width):
            r, g, b, a = icon.getpixel((x, y))
            if a > 128:  # Only draw non-transparent pixels
                pixels.append((offset[0] + x, offset[1] + y, r, g, b))
    return pixels


async def fetch_current_weather():
    """Fetch current weather from OpenWeatherMap"""
    url = f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={OPENWEATHER_API_KEY}&units={UNITS}"
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url)
            data = resp.json()
            
            if resp.status_code != 200:
                print(f"❌ Weather API error: {data.get('message', 'Unknown error')}")
                return None
            
            weather = {
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
            
            print(f"☀️ Weather: {weather['temp']}°F, {weather['description']}")
            return weather
            
        except Exception as e:
            print(f"❌ Error fetching weather: {e}")
            return None


async def fetch_hourly_forecast():
    """Fetch hourly forecast (next 4 hours)"""
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={CITY}&appid={OPENWEATHER_API_KEY}&units={UNITS}&cnt=4"
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url)
            data = resp.json()
            
            if resp.status_code != 200:
                print(f"❌ Forecast API error: {data.get('message', 'Unknown error')}")
                return []
            
            forecasts = []
            for item in data["list"]:
                time = datetime.fromtimestamp(item["dt"]).strftime("%I%p").lstrip("0")
                forecasts.append({
                    "time": time,
                    "temp": round(item["main"]["temp"]),
                    "condition": item["weather"][0]["main"].lower(),
                    "description": item["weather"][0]["description"]
                })
            
            print(f"📅 Fetched {len(forecasts)} hour forecast")
            return forecasts
            
        except Exception as e:
            print(f"❌ Error fetching forecast: {e}")
            return []


async def fetch_daily_forecast():
    """
    Fetch daily forecast (next 2 days).
    Returns high temp for each day with most common condition.
    """
    # Get extended forecast (40 items = ~5 days of 3-hour intervals)
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={CITY}&appid={OPENWEATHER_API_KEY}&units={UNITS}"
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url)
            data = resp.json()
            
            if resp.status_code != 200:
                print(f"❌ Forecast API error: {data.get('message', 'Unknown error')}")
                return []
            
            # Group forecasts by day
            from collections import defaultdict
            daily_data = defaultdict(lambda: {"temps": [], "conditions": []})
            
            for item in data["list"]:
                dt = datetime.fromtimestamp(item["dt"])
                day_key = dt.strftime("%a")  # "Mon", "Tue", etc.
                
                daily_data[day_key]["temps"].append(item["main"]["temp"])
                daily_data[day_key]["conditions"].append(item["weather"][0]["main"].lower())
            
            # Create daily forecasts (skip today, get next 2 days)
            today = datetime.now().strftime("%a")
            forecasts = []
            
            for day_key, day_info in list(daily_data.items())[1:3]:  # Skip first (today), get next 2
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
            
            print(f"📅 Fetched {len(forecasts)} day forecast")
            return forecasts[:2]  # Return only 2 days
            
        except Exception as e:
            print(f"❌ Error fetching daily forecast: {e}")
            return []

