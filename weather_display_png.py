"""
Weather display rendering using PNG upload (FAST!)
Renders weather info as PIL Image for instant upload
"""
from PIL import Image, ImageDraw, ImageFont
from weather_data import WEATHER_COLORS, load_weather_icon


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
    Layout for 40 rows:
    - Top panel (rows 0-19): Current weather
    - Bottom panel (rows 20-39): 2 hourly forecasts
    
    Returns:
        PIL Image (RGB mode, 64xheight)
    """
    # Create black background
    img = Image.new('RGB', (width, height), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    if current:
        # Current weather at top
        render_weather_current(draw, current, offset=(0, 0), width=width)
        
        # Show up to 2 hourly forecasts in bottom panel
        forecast_positions = [20, 28]  # rows 20-27, 28-35
        
        for i, forecast in enumerate(forecasts[:2]):
            render_weather_compact(draw, forecast, offset=(0, forecast_positions[i]), width=width)
    
    return img


def render_weather_bottom_panel(current, forecasts, width=64, height=20):
    """
    Render simplified weather for bottom panel only (when clock is on top).
    Shows current temp + 2 upcoming forecasts side by side.
    
    Layout: [Current] [Forecast1] [Forecast2]
    
    Returns:
        PIL Image (RGB mode, 64x20)
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
    
    # --- LEFT: Current Weather (0-20) ---
    if current:
        temp_color = get_temp_color(current['temp'])
        
        # Small icon
        icon = load_weather_icon(current["condition"], size=(10, 10))
        if icon:
            draw._image.paste(icon, (1, 1), icon if icon.mode == 'RGBA' else None)
        
        # Current temp
        temp_text = f"{current['temp']}"
        draw.text((13, 1), temp_text, fill=temp_color, font=font)
        
        # "NOW" label
        draw.text((2, 11), "NOW", fill=(100, 100, 100), font=small_font)
    
    # --- MIDDLE: Forecast 1 (22-41) ---
    if forecasts and len(forecasts) > 0:
        fc1 = forecasts[0]
        
        # Tiny icon
        icon = load_weather_icon(fc1["condition"], size=(8, 8))
        if icon:
            draw._image.paste(icon, (22, 2), icon if icon.mode == 'RGBA' else None)
        
        temp_text = f"{fc1['temp']}"
        draw.text((32, 0), temp_text, fill=(200, 200, 200), font=forecast_font)
        
        # Time (hour only)
        time_text = fc1['time'][:5]  # "HH:MM" -> show as is
        draw.text((23, 11), time_text, fill=(100, 100, 100), font=small_font)
    
    # --- RIGHT: Forecast 2 (44-63) ---
    if forecasts and len(forecasts) > 1:
        fc2 = forecasts[1]
        
        # Tiny icon
        icon = load_weather_icon(fc2["condition"], size=(8, 8))
        if icon:
            draw._image.paste(icon, (44, 2), icon if icon.mode == 'RGBA' else None)
        
        temp_text = f"{fc2['temp']}"
        draw.text((54, 0), temp_text, fill=(200, 200, 200), font=forecast_font)
        
        # Time (hour only)
        time_text = fc2['time'][:5]  # "HH:MM"
        draw.text((45, 11), time_text, fill=(100, 100, 100), font=small_font)
    
    return img

