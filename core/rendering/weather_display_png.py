"""
Weather display rendering using PNG upload (FAST!)
Renders weather info as PIL Image for instant upload
"""
from PIL import Image, ImageDraw, ImageFont
from core.data.weather_data import WEATHER_COLORS, load_weather_icon
import logging
logger = logging.getLogger(__name__)

def get_temp_color(temp):
    """
    Get color based on temperature:
    - 45 and below: blue
    - 46-60: orange
    - 61+: yellow
    """
    if temp <= 45:
        return (0, 100, 255)  # Blue
    elif temp <= 60:
        return (255, 140, 0)  # Orange
    else:
        return (255, 255, 0)  # Yellow


def render_weather_current(draw, weather, offset=(0,0), width=64):
    """
    Render current weather with icon (16 rows).
    Layout:
      Row 0-7:   [Icon] 45F Clear
      Row 9-16:         H50 L38
    """
    try:
        font = ImageFont.truetype("./fonts/PixelOperator.ttf", 8)
    except OSError:
        font = ImageFont.load_default()
    
    x_start, y_start = offset
    
    # Get temperature-based color
    temp_color = get_temp_color(weather['temp'])
    
    # --- ICON on the left (12x12) ---
    icon = load_weather_icon(weather["condition"], size=(12, 12))
    if icon:
        # Paste icon directly onto the image
        draw._image.paste(icon, (x_start, y_start), icon if icon.mode == 'RGBA' else None)
    
    # Text starts after icon
    text_x = x_start + 13
    
    # --- LINE 1: TEMP + DESCRIPTION ---
    temp_text = f"{weather['temp']}F"
    draw.text((text_x, y_start), temp_text, fill=temp_color, font=font)
    
    # Description (shortened)
    desc_text = weather["description"][:7]
    desc_bbox = font.getbbox(temp_text)
    desc_x = text_x + (desc_bbox[2] - desc_bbox[0]) + 2
    draw.text((desc_x, y_start), desc_text, fill=(180, 180, 180), font=font)
    
    # --- LINE 2: HIGH/LOW ---
    high_low_text = f"H{weather['temp_max']} L{weather['temp_min']}"
    draw.text((text_x, y_start + 9), high_low_text, fill=(200, 200, 200), font=font)


def render_weather_compact(draw, forecast, offset=(0,0), width=64):
    """
    Render hourly forecast in COMPACT format (8 rows).
    Layout: Time (left) + Temp (right)
    """
    try:
        font = ImageFont.truetype("./fonts/PixelOperator.ttf", 8)
    except OSError:
        font = ImageFont.load_default()
    
    x_start, y_start = offset
    
    # Get color based on condition
    condition_color = WEATHER_COLORS.get(forecast["condition"], WEATHER_COLORS["default"])
    
    # --- LEFT: TIME ---
    draw.text((x_start, y_start), forecast["time"], fill=(200, 200, 200), font=font)
    
    # --- RIGHT: TEMP ---
    temp_text = f"{forecast['temp']}F"
    temp_bbox = font.getbbox(temp_text)
    temp_width = temp_bbox[2] - temp_bbox[0]
    temp_x = width - temp_width - 3
    draw.text((temp_x, y_start), temp_text, fill=condition_color, font=font)


def render_weather(current, forecasts, width=64, height=40):
    """
    Render complete weather display as PIL Image.
    Layout adapts to panel height:
    - Top half: Current weather
    - Bottom half: Hourly forecasts (spaced evenly)

    Returns:
        PIL Image (RGB mode)
    """
    # Create black background
    img = Image.new('RGB', (width, height), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)

    if current:
        # Current weather at top
        render_weather_current(draw, current, offset=(0, 0), width=width)

        # Position forecasts in bottom half
        top_half_height = height // 2
        bottom_half_height = height - top_half_height
        num_forecasts = min(len(forecasts), 2)  # Show up to 2 forecasts

        if num_forecasts > 0:
            # Each forecast needs 8 pixels height
            forecast_height = 8
            total_forecast_space_needed = num_forecasts * forecast_height

            # Ensure we don't exceed available space
            if total_forecast_space_needed <= bottom_half_height:
                # Position forecasts starting from top of bottom half
                forecast_positions = []
                for i in range(num_forecasts):
                    y_pos = top_half_height + (i * forecast_height)
                    forecast_positions.append(y_pos)
            else:
                # Distribute evenly in available space
                spacing = bottom_half_height // num_forecasts
                forecast_positions = []
                for i in range(num_forecasts):
                    y_pos = top_half_height + (i * spacing)
                    forecast_positions.append(y_pos)

            for i, forecast in enumerate(forecasts[:num_forecasts]):
                render_weather_compact(draw, forecast, offset=(0, forecast_positions[i]), width=width)
    
    return img


def render_weather_bottom_panel(current, forecasts, width=64, height=20):
    """
    Render simplified weather for bottom panel only (when clock is on top).
    Shows current temp + upcoming forecasts.

    Layout adapts to width: [Current] [Forecast1] [Forecast2...]

    Returns:
        PIL Image (RGB mode)
    """
    img = Image.new('RGB', (width, height), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("./fonts/PixelOperator.ttf", 8)
        forecast_font = ImageFont.truetype("./fonts/PixelOperator.ttf", 10)  # Bigger for forecasts!
        small_font = ImageFont.truetype("./fonts/PixelOperator.ttf", 7)
    except OSError:
        font = ImageFont.load_default()
        forecast_font = font
        small_font = font

    # Calculate section widths based on available space
    num_sections = 1 + len(forecasts[:2])  # Current + up to 2 forecasts
    section_width = width // num_sections

    # --- Current Weather (leftmost section) ---
    if current:
        temp_color = get_temp_color(current['temp'])
        x_offset = 0

        # Small icon
        icon = load_weather_icon(current["condition"], size=(10, 10))
        if icon:
            draw._image.paste(icon, (x_offset + 1, 1), icon if icon.mode == 'RGBA' else None)

        # Current temp
        temp_text = f"{current['temp']}"
        draw.text((x_offset + 13, 1), temp_text, fill=temp_color, font=font)

        # "NOW" label
        draw.text((x_offset + 2, 11), "NOW", fill=(100, 100, 100), font=small_font)

    # --- Forecasts ---
    for i, forecast in enumerate(forecasts[:2]):
        x_offset = (i + 1) * section_width

        # Tiny icon
        icon = load_weather_icon(forecast["condition"], size=(8, 8))
        if icon:
            draw._image.paste(icon, (x_offset + 2, 2), icon if icon.mode == 'RGBA' else None)

        # Temperature
        temp_text = f"{forecast['temp']}"
        draw.text((x_offset + 12, 0), temp_text, fill=(200, 200, 200), font=forecast_font)

        # Time (hour only)
        time_text = forecast['time'][:5]  # "HH:MM"
        draw.text((x_offset + 3, 11), time_text, fill=(100, 100, 100), font=small_font)

    return img

