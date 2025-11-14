"""
Layout template loader with built-in defaults.
"""
from typing import Dict, Any, Optional
import logging
from .template import LayoutTemplate, GameLayoutTemplate, StockLayoutTemplate, ElementSpec

logger = logging.getLogger(__name__)


class LayoutLoader:
    """
    Loads layout templates from config with fallback to defaults.
    """
    
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        """
        Initialize loader.
        
        Args:
            config_dict: Full config dictionary (loads layout_templates section)
        """
        self.config_dict = config_dict or {}
        self.templates = {}
        self._load_templates()
    
    def _load_templates(self):
        """Load all layout templates from config."""
        layout_config = self.config_dict.get('layout_templates', {})
        
        # Get canvas dimensions from display config
        display_config = self.config_dict.get('display', {})
        ipixel_config = display_config.get('ipixel', {})
        panel_width = ipixel_config.get('size_width', 64)
        panel_height = ipixel_config.get('size_height', 20)
        num_panels = len(ipixel_config.get('ble_addresses', []))
        
        # Calculate total canvas size
        canvas_width = panel_width
        canvas_height = panel_height * num_panels if num_panels > 0 else 40
        
        logger.info(f"Canvas dimensions: {canvas_width}×{canvas_height}")
        
        # Load mode-specific templates
        for mode in ['sports', 'stocks', 'weather', 'clock']:
            if mode in layout_config:
                self.templates[mode] = LayoutTemplate.from_dict(
                    mode, 
                    layout_config[mode],
                    canvas_width=canvas_width,
                    canvas_height=canvas_height
                )
                logger.info(f"Loaded custom layout template for {mode}")
            else:
                # Use default template
                self.templates[mode] = self._get_default_template(mode, canvas_width, canvas_height)
                logger.debug(f"Using default layout template for {mode}")
    
    def get_template(self, mode: str) -> LayoutTemplate:
        """
        Get layout template for a mode.
        
        Args:
            mode: Mode name ("sports", "stocks", etc.)
        
        Returns:
            LayoutTemplate (uses default if not configured)
        """
        if mode not in self.templates:
            # Lazy load default
            canvas_width = 64
            canvas_height = 40
            self.templates[mode] = self._get_default_template(mode, canvas_width, canvas_height)
        
        return self.templates[mode]
    
    def _get_default_template(self, mode: str, width: int, height: int) -> LayoutTemplate:
        """
        Get default layout template for a mode.
        
        These defaults replicate the current hardcoded behavior.
        """
        if mode == 'sports':
            return self._get_default_sports_template(width, height)
        elif mode == 'stocks':
            return self._get_default_stocks_template(width, height)
        else:
            # Generic default
            return LayoutTemplate(mode=mode, canvas_width=width, canvas_height=height)
    
    def _get_default_sports_template(self, width: int, height: int) -> LayoutTemplate:
        """
        Default sports layout template (matches current hardcoded behavior).
        
        Optimized for dual 20×64 panels (total 64×40).
        """
        template = LayoutTemplate(
            mode='sports',
            canvas_width=width,
            canvas_height=height,
            logo_enabled=True
        )
        
        # One game - full screen with logos
        template.one_item = GameLayoutTemplate(
            away_logo=ElementSpec(x=2, y=2, width=16, height=16),
            away_score=ElementSpec(x=22, y=2, font_size=14, color='away_team'),
            home_logo=ElementSpec(x=2, y=22, width=16, height=16),
            home_score=ElementSpec(x=22, y=22, font_size=14, color='home_team'),
            period=ElementSpec(x=3, y=2, font_size=8, align='right', color='time'),
            clock=ElementSpec(x=3, y=11, font_size=8, align='right', color='time'),
        )
        
        # Two games - expanded format (20px each)
        template.two_items = {
            'item_height': 20,
            'item_template': GameLayoutTemplate(
                away_text=ElementSpec(x=2, y=1, font_size=10, color='away_team', format='{abbr} {score}'),
                home_text=ElementSpec(x=2, y=11, font_size=10, color='home_team', format='{abbr} {score}'),
                period=ElementSpec(x=4, y=1, font_size=8, align='right', color='time'),
                clock=ElementSpec(x=4, y=11, font_size=8, align='right', color='time'),
            )
        }
        
        # Three games - compact format
        template.three_items = {
            'item_height': 10,
            'item_template': GameLayoutTemplate(
                away_text=ElementSpec(x=1, y=0, font_size=10, color='away_team', format='{abbr} {score}'),
                home_text=ElementSpec(x=32, y=0, font_size=10, color='home_team', format='{abbr} {score}', align='right'),
            )
        }
        
        # Four games - compact format
        template.four_items = {
            'item_height': 10,
            'item_template': GameLayoutTemplate(
                away_text=ElementSpec(x=1, y=0, font_size=10, color='away_team', format='{abbr} {score}'),
                home_text=ElementSpec(x=32, y=0, font_size=10, color='home_team', format='{abbr} {score}', align='right'),
            )
        }
        
        return template
    
    def _get_default_stocks_template(self, width: int, height: int) -> LayoutTemplate:
        """
        Default stocks layout template (matches current hardcoded behavior).
        """
        template = LayoutTemplate(
            mode='stocks',
            canvas_width=width,
            canvas_height=height,
            logo_enabled=False
        )
        
        # One stock - large display
        template.one_item = StockLayoutTemplate(
            symbol=ElementSpec(x=2, y=2, font_size=9, color='white'),
            price=ElementSpec(x=2, y=12, font_size=9, color='change_color'),
            change=ElementSpec(x=2, y=24, font_size=8, color='change_color'),
        )
        
        # Two stocks - split vertically
        template.two_items = {
            'item_height': 20,
            'item_template': StockLayoutTemplate(
                symbol=ElementSpec(x=2, y=0, font_size=8, color='white'),
                price=ElementSpec(x=22, y=0, font_size=8, color='change_color'),
                change=ElementSpec(x=48, y=0, font_size=8, color='change_color'),
            )
        }
        
        # Four stocks - compact
        template.four_items = {
            'item_height': 10,
            'item_template': StockLayoutTemplate(
                symbol=ElementSpec(x=1, y=0, font_size=8, color='white'),
                price=ElementSpec(x=18, y=0, font_size=8, color='change_color'),
                change=ElementSpec(x=42, y=0, font_size=8, color='change_color'),
            )
        }
        
        return template


def load_layout_templates(config_dict: Optional[Dict[str, Any]] = None) -> LayoutLoader:
    """
    Convenience function to load layout templates.
    
    Args:
        config_dict: Full config dictionary
    
    Returns:
        LayoutLoader instance
    """
    return LayoutLoader(config_dict)

