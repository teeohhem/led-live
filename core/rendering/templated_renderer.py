"""
Template-aware renderer for sports, stocks, and other modes.

Uses layout templates to position elements instead of hardcoded coordinates.
"""
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Any, Optional, Tuple, List
import logging

from core.layout import LayoutTemplate, GameLayoutTemplate, StockLayoutTemplate, WeatherLayoutTemplate, ElementSpec

logger = logging.getLogger(__name__)


# Color palette
COLOR_PALETTE = {
    'white': (255, 255, 255),
    'black': (0, 0, 0),
    'gray': (150, 150, 150),
    'red': (255, 0, 0),
    'green': (0, 255, 0),
    'blue': (0, 0, 255),
    'yellow': (255, 255, 0),
    'orange': (255, 165, 0),
    'cyan': (0, 255, 255),
    'magenta': (255, 0, 255),
    # Special dynamic colors (resolved at render time)
    'away_team': None,  # Set based on team
    'home_team': None,
    'time': (255, 255, 0),
    'change_color': None,  # Green/red based on stock movement
}


def resolve_color(color_name: str, context: Dict[str, Any]) -> Tuple[int, int, int]:
    """
    Resolve a color name to RGB tuple.
    
    Args:
        color_name: Color name or tuple
        context: Runtime context (team info, stock data, etc.)
    
    Returns:
        (R, G, B) tuple
    """
    # If already a tuple, return it
    if isinstance(color_name, (tuple, list)) and len(color_name) == 3:
        return tuple(color_name)
    
    # Dynamic color resolution
    if color_name == 'away_team':
        return context.get('away_color', (0, 255, 0))
    elif color_name == 'home_team':
        return context.get('home_color', (255, 0, 0))
    elif color_name == 'change_color':
        is_up = context.get('is_up', True)
        return (0, 255, 0) if is_up else (255, 0, 0)
    
    # Static color lookup
    return COLOR_PALETTE.get(color_name, (255, 255, 255))


def load_font(size: int, font_path: str = "./fonts/PixelOperator.ttf") -> ImageFont:
    """Load font or fallback to default."""
    try:
        return ImageFont.truetype(font_path, size)
    except OSError:
        return ImageFont.load_default()


def get_rendered_bounds(spec: ElementSpec, text: str, canvas_width: int) -> Tuple[int, int, int, int]:
    """
    Return the actual screen bounding box (x, y, w, h) where text would be drawn.

    Uses the same logic as render_element_text so callers never have to
    re-implement alignment math when positioning things relative to text.
    """
    font = load_font(spec.font_size)
    bbox = font.getbbox(text)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    x, y = spec.get_position(canvas_width)
    if spec.align == 'right':
        x = x - text_w
    elif spec.align == 'center':
        x = x - text_w // 2

    return (x, y, text_w, text_h)


def render_element_text(draw: ImageDraw, spec: ElementSpec, text: str, context: Dict[str, Any], canvas_width: int):
    """
    Render a text element using its spec.
    
    Args:
        draw: PIL ImageDraw object
        spec: Element specification
        text: Text to render
        context: Runtime context for color resolution
        canvas_width: Canvas width for alignment
    """
    if not spec:
        return
    
    font = load_font(spec.font_size)
    color = resolve_color(spec.color, context)
    x, y, _, _ = get_rendered_bounds(spec, text, canvas_width)
    draw.text((x, y), text, fill=color, font=font)


def render_element_logo(img: Image, spec: ElementSpec, logo: Optional[Image.Image]):
    """
    Render a logo element using its spec.
    
    Args:
        img: PIL Image to paste onto
        spec: Element specification
        logo: Logo image to paste (RGBA)
    """
    if not spec or not logo:
        return
    
    # Resize logo if dimensions specified
    if spec.width and spec.height:
        logo = logo.resize((spec.width, spec.height), Image.LANCZOS)
    
    # Paste with alpha blending
    img.paste(logo, (spec.x, spec.y), logo)


def format_text(template_str: Optional[str], data: Dict[str, Any]) -> str:
    """
    Format text using template string.
    
    Args:
        template_str: Format string (e.g., "{abbr} {score}")
        data: Data dict with values
    
    Returns:
        Formatted string
    """
    if not template_str:
        return ""
    
    try:
        return template_str.format(**data)
    except KeyError as e:
        logger.warning(f"Missing key {e} in template: {template_str}")
        return template_str


class TemplatedSportsRenderer:
    """
    Renders sports games using layout templates.
    """
    
    def __init__(self, layout_template: LayoutTemplate):
        self.template = layout_template
        self.width = layout_template.canvas_width
        self.height = layout_template.canvas_height
    
    def render_games(self, games: List[Dict[str, Any]], display_type: str = 'live') -> Image.Image:
        """
        Render games using appropriate template.
        
        Args:
            games: List of game dicts
            display_type: 'live' or 'upcoming'
        
        Returns:
            PIL Image
        """
        img = Image.new('RGB', (self.width, self.height), color=(0, 0, 0))
        
        if not games:
            return img
        
        num_games = len(games)
        scenario_template = self.template.get_template_for_count(num_games)
        
        if scenario_template is None:
            logger.error(f"No template for {num_games} games. Add a template for {num_games} items.")
            # Return blank image instead of crashing
            draw = ImageDraw.Draw(img)
            font = load_font(9)
            draw.text((2, 5), f"No template for {num_games} games", fill=(255, 255, 0), font=font)
            draw.text((2, 15), f"Add '{num_games}_items' to template", fill=(180, 180, 180), font=font)
            return img
        
        # Handle single game (full template)
        if num_games == 1 and isinstance(scenario_template, GameLayoutTemplate):
            self._render_single_game(img, games[0], scenario_template, display_type)
        # Handle multi-game scenarios
        elif isinstance(scenario_template, dict):
            self._render_multi_games(img, games, scenario_template, display_type)
        
        return img
    
    def _render_single_game(self, img: Image, game: Dict[str, Any], template: GameLayoutTemplate, display_type: str):
        """Render a single game with full template."""
        draw = ImageDraw.Draw(img)
        
        # Prepare context for color resolution
        from .sports_helpers import get_team_color, load_team_logo
        
        league = game.get('league', '')
        away_name = game['away']
        home_name = game['home']
        is_game_over = game.get('state', '') in ['post', 'completed', 'final']
        
        context = {
            'away_color': (150, 150, 150) if is_game_over else get_team_color(away_name, league, (0, 255, 0)),
            'home_color': (150, 150, 150) if is_game_over else get_team_color(home_name, league, (255, 0, 0)),
        }
        
        # Render away team elements
        if template.away_logo and self.template.logo_enabled:
            logo = load_team_logo(away_name, league, max_size=(
                template.away_logo.width or 16,
                template.away_logo.height or 16
            ))
            render_element_logo(img, template.away_logo, logo)
        
        if template.away_score:
            render_element_text(draw, template.away_score, str(game.get('away_score', 0)), context, self.width)
        
        if template.away_name:
            render_element_text(draw, template.away_name, away_name, context, self.width)
        
        # Render home team elements
        if template.home_logo and self.template.logo_enabled:
            logo = load_team_logo(home_name, league, max_size=(
                template.home_logo.width or 16,
                template.home_logo.height or 16
            ))
            render_element_logo(img, template.home_logo, logo)
        
        if template.home_score:
            render_element_text(draw, template.home_score, str(game.get('home_score', 0)), context, self.width)
        
        if template.home_name:
            render_element_text(draw, template.home_name, home_name, context, self.width)
        
        # Render game status
        is_mlb = game.get('league', '').upper() == 'MLB'
        if display_type == 'live':
            if template.period:
                period_text = "END" if is_game_over else game.get('period', '')
                if period_text:
                    render_element_text(draw, template.period, period_text, context, self.width)
                
                # MLB: draw ▲/▼ pixel triangle above/below the inning number,
                # like a real scoreboard — no horizontal space needed.
                if is_mlb and not is_game_over and period_text:
                    batting_half = game.get('batting_half')
                    if batting_half in ('top', 'bot'):
                        tx, ty, tw, th = get_rendered_bounds(template.period, period_text, self.width)
                        tri_cx = tx + tw // 2   # horizontally centered over the text
                        c = (255, 255, 0)
                        if batting_half == 'top':
                            # ▲ just above the text (clamped so it never goes off the top)
                            tri_y = max(0, ty - 3)
                            draw.point([(tri_cx,     tri_y + 1)], fill=c)
                            draw.point([(tri_cx - 1, tri_y + 2), (tri_cx, tri_y + 2), (tri_cx + 1, tri_y + 2)], fill=c)
                        else:
                            # ▼ just below the text
                            tri_y = ty + th + 5
                            draw.point([(tri_cx - 1, tri_y),     (tri_cx, tri_y),     (tri_cx + 1, tri_y)], fill=c)
                            draw.point([(tri_cx,     tri_y + 1)], fill=c)

            if template.clock and not is_game_over:
                if is_mlb:
                    outs = game.get('outs')
                    clock_text = f"{outs} out" if outs is not None else ''
                else:
                    clock_text = game.get('clock', '')
                if clock_text:
                    render_element_text(draw, template.clock, clock_text, context, self.width)
            
            # MLB batting indicator: small dot to the right of the batting team's score
            if is_mlb and not is_game_over:
                batting_half = game.get('batting_half')
                if batting_half == 'top':
                    score_spec = template.away_score
                    score_val = str(game.get('away_score', 0))
                elif batting_half == 'bot':
                    score_spec = template.home_score
                    score_val = str(game.get('home_score', 0))
                else:
                    score_spec = None
                    score_val = ''
                if score_spec:
                    sx, sy, sw, sh = get_rendered_bounds(score_spec, score_val, self.width)
                    dot_x = sx + sw + 2
                    dot_y = sy + sh // 2
                    draw.ellipse([dot_x - 1, dot_y - 1, dot_x + 1, dot_y + 1], fill=(255, 255, 255))
        else:  # upcoming
            if template.time:
                time_text = game.get('time', '')
                render_element_text(draw, template.time, time_text, context, self.width)
    
    def _render_multi_games(self, img: Image, games: List[Dict[str, Any]], scenario_template: Dict[str, Any], display_type: str):
        """Render multiple games using repeating or per-item templates."""
        from .sports_helpers import get_team_color, load_team_logo
        
        draw = ImageDraw.Draw(img)
        item_height = scenario_template.get('item_height', 20)
        
        # Check if using repeating template or per-item templates
        if 'item_template' in scenario_template:
            # Repeating template
            game_template = scenario_template['item_template']
            templates = [game_template] * len(games)
        elif 'items' in scenario_template:
            # Per-item templates
            templates = scenario_template['items']
        else:
            logger.error("Invalid multi-game template: missing 'item_template' or 'items'")
            return
        
        # Render each game
        for idx, (game, game_template) in enumerate(zip(games, templates)):
            y_offset = idx * item_height
            
            # Prepare context
            league = game.get('league', '')
            away_name = game['away']
            home_name = game['home']
            is_game_over = game.get('state', '') in ['post', 'completed', 'final']
            
            context = {
                'away_color': (150, 150, 150) if is_game_over else get_team_color(away_name, league, (0, 255, 0)),
                'home_color': (150, 150, 150) if is_game_over else get_team_color(home_name, league, (255, 0, 0)),
            }
            
            # Helper to offset element specs
            def offset_spec(spec: Optional[ElementSpec], y_off: int) -> Optional[ElementSpec]:
                if not spec:
                    return None
                # Create new spec with y offset
                import copy
                new_spec = copy.copy(spec)
                new_spec.y = spec.y + y_off
                return new_spec
            
            # Render away team
            if game_template.away_text:
                # Combined text (e.g., "DET 5")
                away_abbr = away_name[:3]
                away_score = game.get('away_score', 0)
                text = format_text(game_template.away_text.format, {
                    'abbr': away_abbr,
                    'name': away_name,
                    'score': away_score
                })
                render_element_text(draw, offset_spec(game_template.away_text, y_offset), text, context, self.width)
            elif game_template.away_score:
                # Separate score
                render_element_text(draw, offset_spec(game_template.away_score, y_offset), str(game.get('away_score', 0)), context, self.width)
            
            # Render home team
            if game_template.home_text:
                home_abbr = home_name[:3]
                home_score = game.get('home_score', 0)
                text = format_text(game_template.home_text.format, {
                    'abbr': home_abbr,
                    'name': home_name,
                    'score': home_score
                })
                render_element_text(draw, offset_spec(game_template.home_text, y_offset), text, context, self.width)
            elif game_template.home_score:
                render_element_text(draw, offset_spec(game_template.home_score, y_offset), str(game.get('home_score', 0)), context, self.width)
            
            # Render game status
            if display_type == 'live':
                if game_template.period:
                    period_text = "END" if is_game_over else game.get('period', '')
                    if period_text:
                        render_element_text(draw, offset_spec(game_template.period, y_offset), period_text, context, self.width)
                
                if game_template.clock and not is_game_over:
                    clock_text = game.get('clock', '')
                    if clock_text:
                        render_element_text(draw, offset_spec(game_template.clock, y_offset), clock_text, context, self.width)


class TemplatedStocksRenderer:
    """
    Renders stock quotes using layout templates.
    """
    
    def __init__(self, layout_template: LayoutTemplate):
        self.template = layout_template
        self.width = layout_template.canvas_width
        self.height = layout_template.canvas_height
    
    def render_stocks(self, quotes: List[Dict[str, Any]]) -> Image.Image:
        """
        Render stock quotes using appropriate template.
        
        Args:
            quotes: List of stock quote dicts
        
        Returns:
            PIL Image
        """
        img = Image.new('RGB', (self.width, self.height), color=(0, 0, 0))
        
        if not quotes:
            draw = ImageDraw.Draw(img)
            font = load_font(9)
            draw.text((2, 15), "No Stock Data", fill=(180, 180, 180), font=font)
            return img
        
        num_stocks = len(quotes)
        scenario_template = self.template.get_template_for_count(num_stocks)
        
        if scenario_template is None:
            logger.error(f"No template for {num_stocks} stocks. Add a template for {num_stocks} items.")
            # Return helpful message instead of crashing
            draw = ImageDraw.Draw(img)
            font = load_font(9)
            draw.text((2, 5), f"No template for {num_stocks} stocks", fill=(255, 255, 0), font=font)
            draw.text((2, 15), f"Add '{num_stocks}_items' to template", fill=(180, 180, 180), font=font)
            return img
        
        # Handle single stock
        if num_stocks == 1 and isinstance(scenario_template, StockLayoutTemplate):
            self._render_single_stock(img, quotes[0], scenario_template)
        # Handle multi-stock scenarios
        elif isinstance(scenario_template, dict):
            self._render_multi_stocks(img, quotes, scenario_template)
        
        return img
    
    def _render_single_stock(self, img: Image, quote: Dict[str, Any], template: StockLayoutTemplate):
        """Render a single stock with full template."""
        draw = ImageDraw.Draw(img)
        
        is_up = quote.get('is_up', True)
        context = {'is_up': is_up}
        
        if template.symbol:
            render_element_text(draw, template.symbol, quote['symbol'], context, self.width)
        
        if template.price:
            price_text = f"${quote['price']:.2f}"
            render_element_text(draw, template.price, price_text, context, self.width)
        
        if template.change or template.change_percent:
            arrow = "▲" if is_up else "▼"
            change_pct = quote['change_percent']
            change_text = f"{arrow} {abs(change_pct):.1f}%"
            spec = template.change or template.change_percent
            render_element_text(draw, spec, change_text, context, self.width)
    
    def _render_multi_stocks(self, img: Image, quotes: List[Dict[str, Any]], scenario_template: Dict[str, Any]):
        """Render multiple stocks using repeating or per-item templates."""
        draw = ImageDraw.Draw(img)
        item_height = scenario_template.get('item_height', 10)
        
        # Get templates
        if 'item_template' in scenario_template:
            stock_template = scenario_template['item_template']
            templates = [stock_template] * len(quotes)
        elif 'items' in scenario_template:
            templates = scenario_template['items']
        else:
            logger.error("Invalid multi-stock template")
            return
        
        # Render each stock
        for idx, (quote, stock_template) in enumerate(zip(quotes, templates)):
            y_offset = idx * item_height
            
            is_up = quote.get('is_up', True)
            context = {'is_up': is_up}
            
            # Helper to offset specs
            def offset_spec(spec: Optional[ElementSpec], y_off: int) -> Optional[ElementSpec]:
                if not spec:
                    return None
                import copy
                new_spec = copy.copy(spec)
                new_spec.y = spec.y + y_off
                return new_spec
            
            if stock_template.symbol:
                render_element_text(draw, offset_spec(stock_template.symbol, y_offset), quote['symbol'][:4], context, self.width)
            
            if stock_template.price:
                price = quote['price']
                if price >= 1000:
                    price_text = f"${price/1000:.1f}k"
                elif price >= 100:
                    price_text = f"${price:.0f}"
                else:
                    price_text = f"${price:.2f}"
                render_element_text(draw, offset_spec(stock_template.price, y_offset), price_text, context, self.width)
            
            if stock_template.change or stock_template.change_percent:
                arrow = "▲" if is_up else "▼"
                change_pct = quote['change_percent']
                change_text = f"{arrow}{abs(change_pct):.1f}%"
                spec = stock_template.change or stock_template.change_percent
                render_element_text(draw, offset_spec(spec, y_offset), change_text, context, self.width)


class TemplatedWeatherRenderer:
    """
    Renders weather information using layout templates.
    """
    
    def __init__(self, layout_template: LayoutTemplate):
        self.template = layout_template
        self.width = layout_template.canvas_width
        self.height = layout_template.canvas_height
    
    def render_weather(self, current_weather: Dict[str, Any], forecasts: List[Dict[str, Any]] = None, 
                      mode: str = 'current') -> Image.Image:
        """
        Render weather display using appropriate template.
        
        Args:
            current_weather: Current weather data dict
            forecasts: Optional list of forecast dicts
            mode: 'current' for current weather or 'forecast' for extended forecast
        
        Returns:
            PIL Image
        """
        img = Image.new('RGB', (self.width, self.height), color=(0, 0, 0))
        
        # Handle extended forecast mode
        if mode == 'forecast' and forecasts:
            return self.render_forecast_extended(forecasts)
        
        if not current_weather:
            draw = ImageDraw.Draw(img)
            font = load_font(9)
            draw.text((2, 15), "No Weather Data", fill=(180, 180, 180), font=font)
            return img
        
        # Use one_item template for current weather
        template = self.template.one_item
        
        if template is None or not isinstance(template, WeatherLayoutTemplate):
            logger.error("No weather template defined")
            draw = ImageDraw.Draw(img)
            font = load_font(9)
            draw.text((2, 5), "No weather template", fill=(255, 255, 0), font=font)
            draw.text((2, 15), "Add 'one_item' to template", fill=(180, 180, 180), font=font)
            return img
        
        self._render_current_weather(img, current_weather, template)
        
        return img
    
    def _render_current_weather(self, img: Image, weather: Dict[str, Any], template: WeatherLayoutTemplate):
        """Render current weather with template."""
        draw = ImageDraw.Draw(img)
        
        # Get temperature-based color
        temp = weather.get('temp', 70)
        if temp <= 45:
            temp_color = (0, 100, 255)  # Blue (cold)
        elif temp <= 60:
            temp_color = (255, 140, 0)  # Orange (cool)
        else:
            temp_color = (255, 255, 0)  # Yellow (warm)
        
        context = {'temp_color': temp_color}
        
        # Render weather icon
        if template.weather_icon:
            from core.data.weather_data import load_weather_icon
            icon = load_weather_icon(
                weather.get('condition', 'clear'),
                size=(template.weather_icon.width or 16, template.weather_icon.height or 16)
            )
            if icon:
                render_element_logo(img, template.weather_icon, icon)
        
        # Render temperature
        if template.temperature:
            temp_text = f"{weather.get('temp', '--')}°F"
            color = resolve_color(template.temperature.color, context) if template.temperature.color != 'white' else temp_color
            spec_with_color = template.temperature
            render_element_text(draw, spec_with_color, temp_text, {'temp_color': color}, self.width)
        
        # Render feels like
        if template.feels_like and 'feels_like' in weather:
            feels_text = f"Feels {weather['feels_like']}°"
            render_element_text(draw, template.feels_like, feels_text, context, self.width)
        
        # Render condition
        if template.condition:
            condition_text = weather.get('description', weather.get('condition', 'N/A'))
            render_element_text(draw, template.condition, condition_text, context, self.width)
        
        # Render short condition (for small displays)
        if template.condition_short:
            condition = weather.get('condition', 'clear')
            short_text = condition[:4].upper()  # First 4 chars
            render_element_text(draw, template.condition_short, short_text, context, self.width)
        
        # Render location
        if template.location and 'zipcode' in weather:
            render_element_text(draw, template.location, weather['zipcode'], context, self.width)
        
        # Render humidity
        if template.humidity and 'humidity' in weather:
            humidity_text = f"{weather['humidity']}%"
            render_element_text(draw, template.humidity, humidity_text, context, self.width)
        
        # Render wind
        if template.wind and 'wind_speed' in weather:
            wind_text = f"{weather['wind_speed']}mph"
            render_element_text(draw, template.wind, wind_text, context, self.width)
        
        # Render high/low temps
        if template.high_temp and 'temp_max' in weather:
            high_text = f"H{weather['temp_max']}°"
            render_element_text(draw, template.high_temp, high_text, context, self.width)
        
        if template.low_temp and 'temp_min' in weather:
            low_text = f"L{weather['temp_min']}°"
            render_element_text(draw, template.low_temp, low_text, context, self.width)
    
    def render_forecast_extended(self, forecasts: List[Dict[str, Any]]) -> Image.Image:
        """
        Render extended forecast with multiple days.
        
        Args:
            forecasts: List of forecast dicts with temp, condition, day info
        
        Returns:
            PIL Image
        """
        img = Image.new('RGB', (self.width, self.height), color=(0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Get forecast_extended template from raw template data
        if not hasattr(self.template, '_raw_data') or 'forecast_extended' not in self.template._raw_data:
            draw.text((2, 5), "No forecast template", fill=(255, 255, 0), font=load_font(9))
            draw.text((2, 15), "Add 'forecast_extended'", fill=(180, 180, 180), font=load_font(8))
            return img
        
        forecast_template = self.template._raw_data['forecast_extended']
        item_width = forecast_template.get('item_width', 16)
        item_template = forecast_template.get('item_template', {})
        
        # Limit to what fits on screen
        max_items = self.width // item_width
        forecasts_to_show = forecasts[:max_items]
        
        from core.data.weather_data import load_weather_icon
        from datetime import datetime
        
        for idx, forecast in enumerate(forecasts_to_show):
            x_offset = idx * item_width
            
            # Parse day name (abbreviate if needed)
            day_str = forecast.get('day', '')
            if isinstance(forecast.get('date'), str):
                try:
                    date_obj = datetime.fromisoformat(forecast['date'])
                    day_str = date_obj.strftime('%a')[:3]  # Mon, Tue, etc.
                except:
                    pass
            elif not day_str:
                day_str = f"D{idx+1}"
            
            # Render day label
            if 'day' in item_template:
                spec = self._offset_spec_x(item_template['day'], x_offset, item_width)
                render_element_text(draw, spec, day_str, {}, self.width)
            
            # Render weather icon
            if 'weather_icon' in item_template:
                icon_spec = item_template['weather_icon']
                icon_size = (icon_spec.get('width', 12), icon_spec.get('height', 12))
                icon = load_weather_icon(forecast.get('condition', 'clear'), size=icon_size)
                
                if icon:
                    # Center icon in item width
                    icon_x = x_offset + (item_width - icon_size[0]) // 2
                    icon_y = icon_spec.get('y', 7)
                    img.paste(icon, (icon_x, icon_y), icon if icon.mode == 'RGBA' else None)
            
            # Render high temp
            if 'high_temp' in item_template:
                high = forecast.get('high', forecast.get('temp', '--'))
                temp_text = f"{int(high)}°" if isinstance(high, (int, float)) else str(high)
                spec = self._offset_spec_x(item_template['high_temp'], x_offset, item_width)
                render_element_text(draw, spec, temp_text, {}, self.width)
            
            # Render low temp
            if 'low_temp' in item_template:
                low = forecast.get('low', '--')
                temp_text = f"{int(low)}°" if isinstance(low, (int, float)) else str(low)
                spec = self._offset_spec_x(item_template['low_temp'], x_offset, item_width)
                render_element_text(draw, spec, temp_text, {}, self.width)
        
        return img
    
    def _offset_spec_x(self, spec_dict: Dict, x_offset: int, item_width: int) -> ElementSpec:
        """Create ElementSpec from dict and offset x coordinate."""
        from core.layout.template import ElementSpec
        
        # Handle center alignment
        align = spec_dict.get('align', 'left')
        base_x = spec_dict.get('x', 0)
        
        if align == 'center':
            actual_x = x_offset + item_width // 2
        else:
            actual_x = x_offset + base_x
        
        return ElementSpec(
            x=actual_x,
            y=spec_dict.get('y', 0),
            font_size=spec_dict.get('font_size', 8),
            color=spec_dict.get('color', 'white'),
            align=align
        )

