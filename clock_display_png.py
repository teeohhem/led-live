"""
Custom clock rendering with theme support (PNG upload)
"""
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import json
import os
from pathlib import Path


# --- LOAD CUSTOM THEMES ---
def load_custom_themes():
    """Load custom themes from custom_themes.json if it exists"""
    custom_themes = {}
    themes_file = Path(__file__).parent / "custom_themes.json"
    
    if themes_file.exists():
        try:
            with open(themes_file, 'r') as f:
                custom_themes = json.load(f)
            print(f"✅ Loaded {len(custom_themes)} custom clock theme(s) from custom_themes.json")
        except Exception as e:
            print(f"⚠️  Error loading custom_themes.json: {e}")
    
    return custom_themes


# --- BUILT-IN THEMES ---
BUILT_IN_THEMES = {
    "stranger_things": {
        "bg_color": (0, 0, 0),  # Black background
        "time_color": (255, 50, 50),  # Red text (like the show logo)
        "date_color": (150, 150, 150),  # Gray date
        "font_time": "./fonts/PixelOperator.ttf",
        "font_date": "./fonts/PixelOperator.ttf",
        "time_size": 16,
        "date_size": 8,
        "glow": True,  # Add a glow effect
        "glow_color": (100, 0, 0),  # Dark red glow
    },
    "classic": {
        "bg_color": (0, 0, 0),
        "time_color": (0, 255, 255),  # Cyan
        "date_color": (255, 255, 0),  # Yellow
        "font_time": "./fonts/PixelOperator.ttf",
        "font_date": "./fonts/PixelOperator.ttf",
        "time_size": 14,
        "date_size": 8,
        "glow": False,
    },
    "matrix": {
        "bg_color": (0, 0, 0),
        "time_color": (0, 255, 0),  # Green
        "date_color": (0, 180, 0),  # Darker green
        "font_time": "./fonts/PixelOperator.ttf",
        "font_date": "./fonts/PixelOperator.ttf",
        "time_size": 14,
        "date_size": 8,
        "glow": False,
    },
}

# Merge built-in themes with custom themes (custom themes override built-in if same name)
THEMES = {**BUILT_IN_THEMES, **load_custom_themes()}


def render_clock(width=64, height=20, theme="stranger_things", hour24=False):
    """
    Render a themed clock display.
    
    Args:
        width: Display width (default 64)
        height: Display height (default 20 for top panel)
        theme: Theme name from THEMES dict
        hour24: Use 24-hour format (True) or 12-hour with AM/PM (False)
    
    Returns:
        PIL Image (RGB mode)
    """
    theme_config = THEMES.get(theme, THEMES["classic"])
    
    # Create image
    img = Image.new('RGB', (width, height), color=theme_config["bg_color"])
    draw = ImageDraw.Draw(img)
    
    # Load fonts
    try:
        time_font = ImageFont.truetype(theme_config["font_time"], theme_config["time_size"])
        date_font = ImageFont.truetype(theme_config["font_date"], theme_config["date_size"])
    except OSError:
        time_font = ImageFont.load_default()
        date_font = ImageFont.load_default()
    
    # Get current time
    now = datetime.now()
    
    # Format time string
    if hour24:
        time_str = now.strftime("%H:%M")
    else:
        time_str = now.strftime("%I:%M")
        if time_str.startswith("0"):
            time_str = time_str[1:]  # Remove leading zero
    
    # Format date string (abbreviated for small display)
    date_str = now.strftime("%a %m/%d")  # e.g., "Mon 11/10"
    
    # Draw time (top portion of display)
    time_bbox = time_font.getbbox(time_str)
    time_width = time_bbox[2] - time_bbox[0]
    time_x = (width - time_width) // 2
    time_y = -2  # Move up to eliminate top padding
    
    # Add glow effect if enabled
    if theme_config.get("glow"):
        glow_color = theme_config["glow_color"]
        # Draw glow slightly offset
        for offset in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            draw.text((time_x + offset[0], time_y + offset[1]), time_str, 
                     fill=glow_color, font=time_font)
    
    # Draw main time text
    draw.text((time_x, time_y), time_str, fill=theme_config["time_color"], font=time_font)
    
    # Draw date at bottom (if space allows)
    if height >= 20:
        date_bbox = date_font.getbbox(date_str)
        date_width = date_bbox[2] - date_bbox[0]
        date_x = (width - date_width) // 2
        date_y = height - 8  # Very bottom of display
        draw.text((date_x, date_y), date_str, fill=theme_config["date_color"], font=date_font)
    
    return img


def render_clock_with_weather_split(current_weather, forecasts, theme="stranger_things", hour24=False):
    """
    Render clock on top panel (20px) and weather on bottom panel (20px).
    
    Args:
        current_weather: Current weather dict from weather_data
        forecasts: List of forecast dicts from weather_data
        theme: Clock theme name
        hour24: Use 24-hour format
    
    Returns:
        PIL Image (RGB mode, 64x40)
    """
    from weather_display_png import render_weather_bottom_panel
    
    # Create full 64x40 image
    img = Image.new('RGB', (64, 40), color=(0, 0, 0))
    
    # Render clock on top (64x20)
    clock_img = render_clock(width=64, height=20, theme=theme, hour24=hour24)
    img.paste(clock_img, (0, 0))
    
    # Render weather on bottom (64x20)
    weather_img = render_weather_bottom_panel(current_weather, forecasts, width=64, height=20)
    img.paste(weather_img, (0, 20))
    
    return img

