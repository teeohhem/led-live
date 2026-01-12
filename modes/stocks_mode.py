"""
Stocks mode - displays stock market quotes.
"""
from datetime import datetime
from typing import Optional
from PIL import Image
import logging

from .base_mode import BaseMode
from core.data import stocks_fetcher
from core.layout import LayoutLoader
from core.rendering.templated_renderer import TemplatedStocksRenderer

logger = logging.getLogger(__name__)


class StocksMode(BaseMode):
    """Stock market display mode."""
    
    def __init__(self, config):
        super().__init__("stocks", config)
        self.quotes = []
        self.prev_snapshot = None
        
        # Config
        self.check_interval = config.get('STOCKS_CHECK_INTERVAL', 300)
        self.refresh_interval = config.get('DISPLAY_STOCKS_REFRESH_INTERVAL', 2)
        
        # Load layout template (required)
        try:
            from config import get_all_config
            config_dict = get_all_config()
            loader = LayoutLoader(config_dict)
            layout_template = loader.get_template('stocks')
            self.layout_renderer = TemplatedStocksRenderer(layout_template)
            logger.info("Using templated stocks renderer")
        except Exception as e:
            logger.error(f"Failed to load layout template: {e}")
            raise RuntimeError("Stocks mode requires layout templates. Check core/layout/templates/")
    
    async def fetch_data(self) -> bool:
        """Fetch stock quotes."""
        try:
            # Use module-level fetcher with automatic caching
            self.quotes = await stocks_fetcher.get_cached_or_fetch()
            self.last_fetch = datetime.now()
            logger.info(f"Fetched {len(self.quotes)} stock quotes")
            return True
        except Exception as e:
            logger.error(f"Error fetching stocks: {e}")
            return False
    
    def has_data(self) -> bool:
        """Check if we have quote data."""
        return len(self.quotes) > 0
    
    def should_fetch(self, now: datetime) -> bool:
        """Check if data needs updating."""
        if self.last_fetch is None:
            return True
        return (now - self.last_fetch).total_seconds() >= self.check_interval
    
    def should_render(self, now: datetime) -> bool:
        """Check if re-render is needed."""
        # Create snapshot for comparison
        current_snapshot = [
            (q['symbol'], q['price'], q['change_percent'])
            for q in self.quotes
        ]
        
        # Data changed?
        data_changed = current_snapshot != self.prev_snapshot
        
        # Periodic refresh needed?
        needs_refresh = (
            self.last_render is None or
            (now - self.last_render).total_seconds() >= self.refresh_interval
        )
        
        if data_changed:
            self.prev_snapshot = current_snapshot
            return True
        
        return needs_refresh
    
    async def render(self, width: int, height: int) -> Optional[Image.Image]:
        """Render stock display."""
        return self.layout_renderer.render_stocks(self.quotes)
    
    def has_priority(self) -> bool:
        """Stocks never have priority."""
        return False

