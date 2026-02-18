"""
Stocks component for displaying stock quotes.
"""

from typing import Optional, Any, List, Dict
from PIL import Image
from .base import Component


class StocksComponent(Component):
    """
    Displays stock quotes with prices and changes.
    
    Config options:
        - symbols: List of stock symbols (default: from config)
        - screener: Use screener instead ('GAINERS', 'LOSERS', 'MOST_ACTIVE')
        - limit: Max stocks to show (default: based on height)
    """
    
    async def fetch_data(self) -> Optional[List[Dict[str, Any]]]:
        """Fetch stock quote data."""
        from core.data import stocks_fetcher, ScreenerType
        
        try:
            # Check if using screener
            screener_type = self.config.get('screener', None)
            
            if screener_type:
                # Use screener
                screener = ScreenerType[screener_type]
                limit = self.config.get('limit', 10)
                quotes = await stocks_fetcher.fetch_screener(screener, limit=limit)
            else:
                # Use specific symbols or default
                symbols = self.config.get('symbols', None)
                quotes = await stocks_fetcher.get_cached_or_fetch()
            
            # Limit to max number
            limit = self.config.get('limit', None)
            if limit and quotes:
                quotes = quotes[:limit]
            
            return quotes
        except Exception as e:
            self.logger.error(f"Failed to fetch stocks: {e}")
            return None
    
    def render(self, data: Optional[List[Dict[str, Any]]] = None) -> Image.Image:
        """
        Render stock quotes.
        
        Args:
            data: List of quote dicts from fetch_data()
        
        Returns:
            PIL Image
        """
        from core.rendering.templated_renderer import TemplatedStocksRenderer
        from core.layout.loader import LayoutLoader
        from config import get_all_config
        
        # Load stocks template for this size
        config_dict = get_all_config()
        loader = LayoutLoader(config_dict)
        
        # Get template matching our dimensions
        layout = loader.get_layout_for_dimensions(self.width, self.height)
        renderer = TemplatedStocksRenderer(layout)
        
        return renderer.render_stocks(data or [])


