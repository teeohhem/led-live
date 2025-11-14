"""
Template-aware renderer for sports, stocks, and other modes.

Uses layout templates to position elements instead of hardcoded coordinates.
"""
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Any, Optional, Tuple, List
import logging

from core.layout import LayoutTemplate, GameLayoutTemplate, StockLayoutTemplate, ElementSpec

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
    x, y = spec.get_position(canvas_width)
    
    # Handle right alignment
    if spec.align == 'right':
        bbox = font.getbbox(text)
        text_width = bbox[2] - bbox[0]
        x = x - text_width
    elif spec.align == 'center':
        bbox = font.getbbox(text)
        text_width = bbox[2] - bbox[0]
        x = x - (text_width // 2)
    
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
            logger.warning(f"No template for {num_games} games, using fallback")
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
        from core.rendering.sports_display_png import get_team_color, load_team_logo
        
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
        if display_type == 'live':
            if template.period:
                period_text = "END" if is_game_over else game.get('period', '')
                if period_text:
                    render_element_text(draw, template.period, period_text, context, self.width)
            
            if template.clock and not is_game_over:
                clock_text = game.get('clock', '')
                if clock_text:
                    render_element_text(draw, template.clock, clock_text, context, self.width)
        else:  # upcoming
            if template.time:
                time_text = game.get('time', '')
                render_element_text(draw, template.time, time_text, context, self.width)
    
    def _render_multi_games(self, img: Image, games: List[Dict[str, Any]], scenario_template: Dict[str, Any], display_type: str):
        """Render multiple games using repeating or per-item templates."""
        from core.rendering.sports_display_png import get_team_color, load_team_logo
        
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
            logger.warning(f"No template for {num_stocks} stocks, using fallback")
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

