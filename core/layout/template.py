"""
Layout template data structures.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Tuple


@dataclass
class ElementSpec:
    """
    Specification for a single UI element (logo, text, score, etc.)
    
    Attributes:
        x: X position (pixels from left)
        y: Y position (pixels from top)
        width: Optional width constraint
        height: Optional height constraint
        font_size: Font size in pixels
        color: Color name or RGB tuple (resolved at render time)
        align: Text alignment ("left", "right", "center")
        format: Format string for text (e.g., "{abbr} {score}")
        anchor: PIL anchor point for text ("lt", "rt", etc.)
    """
    x: int = 0
    y: int = 0
    width: Optional[int] = None
    height: Optional[int] = None
    font_size: int = 10
    color: str = "white"  # Color name, resolved at render time
    align: str = "left"
    format: Optional[str] = None
    anchor: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ElementSpec':
        """Create ElementSpec from config dict."""
        return cls(
            x=data.get('x', 0),
            y=data.get('y', 0),
            width=data.get('width'),
            height=data.get('height'),
            font_size=data.get('font_size', 10),
            color=data.get('color', 'white'),
            align=data.get('align', 'left'),
            format=data.get('format'),
            anchor=data.get('anchor'),
        )
    
    def get_position(self, parent_width: int = 0) -> Tuple[int, int]:
        """
        Get actual position, accounting for alignment.
        
        Args:
            parent_width: Width of parent container (for right-alignment)
        
        Returns:
            (x, y) tuple
        """
        x = self.x
        if self.align == "right" and parent_width > 0:
            # x is offset from right edge
            x = parent_width - self.x
        elif self.align == "center" and parent_width > 0:
            # x is offset from center
            x = (parent_width // 2) + self.x
        
        return (x, self.y)


@dataclass
class GameLayoutTemplate:
    """
    Layout template for rendering a single game (sports).
    
    Contains element specs for all game components.
    """
    # Team 1 (away) elements
    away_logo: Optional[ElementSpec] = None
    away_name: Optional[ElementSpec] = None
    away_score: Optional[ElementSpec] = None
    away_text: Optional[ElementSpec] = None  # Combined text (e.g., "DET 5")
    
    # Team 2 (home) elements
    home_logo: Optional[ElementSpec] = None
    home_name: Optional[ElementSpec] = None
    home_score: Optional[ElementSpec] = None
    home_text: Optional[ElementSpec] = None
    
    # Game status elements
    period: Optional[ElementSpec] = None
    clock: Optional[ElementSpec] = None
    time: Optional[ElementSpec] = None  # For upcoming games
    separator: Optional[ElementSpec] = None  # Visual separator (e.g., "@")
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameLayoutTemplate':
        """Create GameLayoutTemplate from config dict."""
        def make_spec(key: str) -> Optional[ElementSpec]:
            return ElementSpec.from_dict(data[key]) if key in data else None
        
        return cls(
            away_logo=make_spec('away_logo'),
            away_name=make_spec('away_name'),
            away_score=make_spec('away_score'),
            away_text=make_spec('away_text'),
            home_logo=make_spec('home_logo'),
            home_name=make_spec('home_name'),
            home_score=make_spec('home_score'),
            home_text=make_spec('home_text'),
            period=make_spec('period'),
            clock=make_spec('clock'),
            time=make_spec('time'),
            separator=make_spec('separator'),
        )


@dataclass
class StockLayoutTemplate:
    """Layout template for rendering a single stock quote."""
    symbol: Optional[ElementSpec] = None
    name: Optional[ElementSpec] = None
    price: Optional[ElementSpec] = None
    change: Optional[ElementSpec] = None
    change_percent: Optional[ElementSpec] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StockLayoutTemplate':
        """Create StockLayoutTemplate from config dict."""
        def make_spec(key: str) -> Optional[ElementSpec]:
            return ElementSpec.from_dict(data[key]) if key in data else None
        
        return cls(
            symbol=make_spec('symbol'),
            name=make_spec('name'),
            price=make_spec('price'),
            change=make_spec('change'),
            change_percent=make_spec('change_percent'),
        )


@dataclass
class LayoutTemplate:
    """
    Complete layout template for a display mode.
    
    Contains scenario-based templates (one_game, two_games, etc.)
    with positioning for each element.
    """
    mode: str  # Mode name (sports, stocks, etc.)
    canvas_width: int = 64
    canvas_height: int = 40
    logo_enabled: bool = True
    
    # Scenario-based templates
    one_item: Optional[Any] = None  # GameLayoutTemplate or StockLayoutTemplate
    two_items: Optional[Dict[str, Any]] = None
    three_items: Optional[Dict[str, Any]] = None
    four_items: Optional[Dict[str, Any]] = None
    multi_items: Optional[Dict[str, Any]] = None  # 5+ items
    
    @classmethod
    def from_dict(cls, mode: str, data: Dict[str, Any], canvas_width: int = 64, canvas_height: int = 40) -> 'LayoutTemplate':
        """
        Create LayoutTemplate from config dict.
        
        Args:
            mode: Mode name ("sports", "stocks")
            data: Config data from layout_templates section
            canvas_width: Display width
            canvas_height: Display height
        """
        template = cls(
            mode=mode,
            canvas_width=canvas_width,
            canvas_height=canvas_height,
            logo_enabled=data.get('logo_enabled', True),
        )
        
        # Load scenario templates based on mode
        if mode == 'sports':
            if 'one_game' in data:
                template.one_item = GameLayoutTemplate.from_dict(data['one_game'])
            if 'two_games' in data:
                template.two_items = cls._load_multi_template(data['two_games'], GameLayoutTemplate)
            if 'three_games' in data:
                template.three_items = cls._load_multi_template(data['three_games'], GameLayoutTemplate)
            if 'four_games' in data:
                template.four_items = cls._load_multi_template(data['four_games'], GameLayoutTemplate)
        elif mode == 'stocks':
            if 'one_stock' in data:
                template.one_item = StockLayoutTemplate.from_dict(data['one_stock'])
            if 'two_stocks' in data:
                template.two_items = cls._load_multi_template(data['two_stocks'], StockLayoutTemplate)
            if 'four_stocks' in data:
                template.four_items = cls._load_multi_template(data['four_stocks'], StockLayoutTemplate)
        
        return template
    
    @staticmethod
    def _load_multi_template(data: Dict[str, Any], template_class) -> Dict[str, Any]:
        """
        Load multi-item template (e.g., two_games with item_height and item_template).
        
        Returns dict with:
            - item_height: Height per item
            - item_template: Template to repeat for each item
            - items: Optional list of per-item templates (overrides item_template)
        """
        result = {
            'item_height': data.get('item_height', data.get('game_height', data.get('stock_height', 20))),
        }
        
        # Check if using repeating template or per-item templates
        if 'item_template' in data or 'game_template' in data or 'stock_template' in data:
            # Repeating template (same layout for each item)
            template_data = data.get('item_template') or data.get('game_template') or data.get('stock_template')
            result['item_template'] = template_class.from_dict(template_data)
        elif 'items' in data or 'games' in data or 'stocks' in data:
            # Per-item templates (custom layout for each position)
            items_data = data.get('items') or data.get('games') or data.get('stocks')
            result['items'] = [template_class.from_dict(item) for item in items_data]
        
        return result
    
    def get_template_for_count(self, count: int) -> Optional[Any]:
        """
        Get appropriate template based on item count.
        
        Args:
            count: Number of items to display
        
        Returns:
            Template for that scenario, or None if not defined
        """
        if count == 1:
            return self.one_item
        elif count == 2:
            return self.two_items
        elif count == 3:
            return self.three_items
        elif count == 4:
            return self.four_items
        else:
            return self.multi_items

