"""
Stock market display rendering as PNG
"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path


def render_stocks(quotes, width=64, height=40):
    """
    Render stock quotes as a PNG image.
    
    Args:
        quotes: List of stock quote dicts from stocks_data.py
        width: Image width (default 64)
        height: Image height (default 40)
    
    Returns:
        PIL Image (RGB mode)
    """
    # Create blank image
    img = Image.new('RGB', (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Load fonts
    font_path = Path(__file__).parent / "fonts" / "PixelOperator.ttf"
    
    try:
        font_main = ImageFont.truetype(str(font_path), 9)
        font_small = ImageFont.truetype(str(font_path), 8)
    except:
        font_main = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    if not quotes:
        # No data - show message
        draw.text((2, 15), "No Stock Data", fill=(180, 180, 180), font=font_main)
        return img
    
    # Determine layout based on number of stocks
    num_stocks = len(quotes)
    
    if num_stocks == 1:
        # Single stock - large display
        render_single_stock(draw, quotes[0], width, height, font_main, font_small)
    elif num_stocks == 2:
        # Two stocks - one per panel (20px each)
        render_stock_compact(draw, quotes[0], y_offset=2, font_main=font_main, font_small=font_small)
        render_stock_compact(draw, quotes[1], y_offset=22, font_main=font_main, font_small=font_small)
    elif num_stocks == 3:
        # Three stocks - compact layout
        render_stock_compact(draw, quotes[0], y_offset=2, font_main=font_main, font_small=font_small)
        render_stock_compact(draw, quotes[1], y_offset=14, font_main=font_main, font_small=font_small)
        render_stock_compact(draw, quotes[2], y_offset=26, font_main=font_main, font_small=font_small)
    else:
        # Four or more stocks - very compact
        y_positions = [2, 12, 22, 32]
        for i, quote in enumerate(quotes[:4]):  # Show max 4
            render_stock_mini(draw, quote, y_offset=y_positions[i], font_small=font_small)
    
    return img


def render_single_stock(draw, quote, width, height, font_main, font_small):
    """Render a single stock with large text"""
    symbol = quote['symbol']
    price = quote['price']
    change_pct = quote['change_percent']
    is_up = quote['is_up']
    
    # Color: green for up, red for down
    price_color = (0, 255, 0) if is_up else (255, 0, 0)
    arrow = "▲" if is_up else "▼"
    
    # Symbol at top
    draw.text((2, 2), symbol, fill=(255, 255, 255), font=font_main)
    
    # Price
    price_text = f"${price:.2f}"
    draw.text((2, 12), price_text, fill=price_color, font=font_main)
    
    # Change percentage
    change_text = f"{arrow} {abs(change_pct):.2f}%"
    draw.text((2, 24), change_text, fill=price_color, font=font_small)


def render_stock_compact(draw, quote, y_offset, font_main, font_small):
    """Render stock in compact format (fits in ~12px height)"""
    symbol = quote['symbol']
    price = quote['price']
    change_pct = quote['change_percent']
    is_up = quote['is_up']
    
    # Color: green for up, red for down
    color = (0, 255, 0) if is_up else (255, 0, 0)
    arrow = "▲" if is_up else "▼"
    
    # Symbol on left
    draw.text((2, y_offset), symbol, fill=(255, 255, 255), font=font_small)
    
    # Price in middle
    price_text = f"${price:.2f}"
    draw.text((22, y_offset), price_text, fill=color, font=font_small)
    
    # Change on right
    change_text = f"{arrow}{abs(change_pct):.1f}%"
    draw.text((48, y_offset), change_text, fill=color, font=font_small)


def render_stock_mini(draw, quote, y_offset, font_small):
    """Render stock in mini format (fits in ~10px height)"""
    symbol = quote['symbol']
    price = quote['price']
    change_pct = quote['change_percent']
    is_up = quote['is_up']
    
    # Color: green for up, red for down
    color = (0, 255, 0) if is_up else (255, 0, 0)
    arrow = "▲" if is_up else "▼"
    
    # Symbol
    draw.text((1, y_offset), symbol[:4], fill=(255, 255, 255), font=font_small)
    
    # Price
    if price >= 1000:
        price_text = f"${price/1000:.1f}k"
    elif price >= 100:
        price_text = f"${price:.0f}"
    else:
        price_text = f"${price:.1f}"
    draw.text((18, y_offset), price_text, fill=color, font=font_small)
    
    # Change
    change_text = f"{arrow}{abs(change_pct):.1f}%"
    draw.text((42, y_offset), change_text, fill=color, font=font_small)


if __name__ == "__main__":
    # Test rendering
    test_quotes = [
        {
            'symbol': 'AAPL',
            'price': 185.50,
            'change': 2.50,
            'change_percent': 1.37,
            'is_up': True,
            'name': 'Apple Inc.'
        },
        {
            'symbol': 'GOOGL',
            'price': 142.15,
            'change': -1.25,
            'change_percent': -0.87,
            'is_up': False,
            'name': 'Alphabet Inc.'
        },
        {
            'symbol': 'TSLA',
            'price': 238.72,
            'change': 9.50,
            'change_percent': 4.15,
            'is_up': True,
            'name': 'Tesla Inc.'
        },
        {
            'symbol': 'MSFT',
            'price': 378.91,
            'change': 3.22,
            'change_percent': 0.86,
            'is_up': True,
            'name': 'Microsoft Corp.'
        }
    ]
    
    # Test different layouts
    for count in [1, 2, 3, 4]:
        img = render_stocks(test_quotes[:count], 64, 40)
        img.save(f"test_stocks_{count}.png")
        print(f"✅ Saved test_stocks_{count}.png")

