"""
Ticker mode - scrolling display that can composite multiple modes.

Users can configure which modes to include in the ticker:
- sports (upcoming games)
- stocks (market quotes)
- weather (forecast)
- custom text

Each mode provides its own ticker rendering with logos, colors, etc.
"""
from datetime import datetime
from typing import Optional, List
from PIL import Image
import asyncio
import logging

from .base_mode import BaseMode

logger = logging.getLogger(__name__)


class TickerMode(BaseMode):
    """
    Ticker display mode.
    
    Composites content from multiple modes into a scrolling ticker.
    Each included mode provides its own ticker segment rendering.
    """
    
    def __init__(self, config):
        super().__init__("ticker", config)
        
        # Config
        self.scroll_speed = config.get('TICKER_SCROLL_SPEED', 3)
        self.refresh_interval = config.get('TICKER_REFRESH_INTERVAL', 30)
        
        # Load ticker-specific configs
        from config_loader import ConfigLoader
        cfg = ConfigLoader()
        
        # Check layout mode
        self.layout = cfg.get_string('ticker.layout', 'single')
        
        # Load configuration based on layout
        if self.layout == 'multi':
            # Multi-panel mode - ticker + static panel design
            self.ticker_panel_idx = cfg.get_int('ticker.ticker_panel', 0)
            self.static_panel_idx = cfg.get_int('ticker.static_panel', 1)
            
            # Ticker panel config
            self.ticker_modes = cfg.get_list('ticker.ticker.modes', ['sports'])
            self.ticker_sports_source = cfg.get_string('ticker.ticker.sports.source', 'all_live')
            self.ticker_sports_max = cfg.get_int('ticker.ticker.sports.max_games', 15)
            self.ticker_stocks_source = cfg.get_string('ticker.ticker.stocks.source', 'gainers')
            self.ticker_stocks_max = cfg.get_int('ticker.ticker.stocks.max_symbols', 10)
            
            # Static panel config
            self.static_mode = cfg.get_string('ticker.static.mode', 'stocks')
            self.static_sports_source = cfg.get_string('ticker.static.sports.source', 'my_teams')
            self.static_sports_max = cfg.get_int('ticker.static.sports.max_games', 4)
            self.static_stocks_source = cfg.get_string('ticker.static.stocks.source', 'gainers')
            self.static_stocks_max = cfg.get_int('ticker.static.stocks.max_symbols', 4)
        else:
            # Single-mode config
            self.ticker_modes = cfg.get_list('ticker.single.modes', ['sports', 'stocks'])
            self.sports_source = cfg.get_string('ticker.single.sports.source', 'my_teams')
            self.sports_max = cfg.get_int('ticker.single.sports.max_games', 10)
            self.stocks_source = cfg.get_string('ticker.single.stocks.source', 'my_symbols')
            self.stocks_max = cfg.get_int('ticker.single.stocks.max_symbols', 10)
        
        # Data storage
        self.ticker_segments = []  # Segments for scrolling ticker
        self.ticker_frames = []  # Frames for scrolling ticker
        self.ticker_gif = None  # GIF bytes for ticker
        self.static_images = []  # Multiple static "pages" to cycle through
        self.static_data = None  # Data for static panel
        self.static_page_index = 0  # Current page being displayed
        self.static_page_duration = 5  # Seconds per page
    
    async def fetch_data(self) -> bool:
        """Fetch data for ticker and static content."""
        try:
            if self.layout == 'single':
                return await self._fetch_single_mode()
            else:
                return await self._fetch_ticker_plus_static_mode()
        except Exception as e:
            logger.error(f"Error fetching ticker data: {e}")
            return False
    
    async def _fetch_single_mode(self):
        """Fetch data for single-panel ticker (original behavior)."""
        self.segments = []
        
        # Collect ticker segments from configured modes
        if 'sports' in self.ticker_modes:
            segment = await self._fetch_sports_segment_single()
            if segment:
                self.segments.append(segment)
        
        if 'stocks' in self.ticker_modes:
            segment = await self._fetch_stocks_segment_single()
            if segment:
                self.segments.append(segment)
        
        if 'weather' in self.ticker_modes:
            segment = await self._fetch_weather_segment()
            if segment:
                self.segments.append(segment)
        
        self.last_fetch = datetime.now()
        return len(self.segments) > 0
    
    async def _fetch_ticker_plus_static_mode(self):
        """Fetch data for ticker panel (scrolling) + static panel."""
        # Fetch ticker segments
        self.ticker_segments = []
        
        logger.info(f"Fetching ticker data for panel {self.ticker_panel_idx}: {self.ticker_modes}")
        
        if 'sports' in self.ticker_modes:
            segment = await self._fetch_sports_segment_ticker()
            if segment:
                self.ticker_segments.append(segment)
        
        if 'stocks' in self.ticker_modes:
            segment = await self._fetch_stocks_segment_ticker()
            if segment:
                self.ticker_segments.append(segment)
        
        # Fetch static panel data
        logger.info(f"Fetching static data for panel {self.static_panel_idx}: {self.static_mode}")
        self.static_data = await self._fetch_static_panel_data()
        
        self.last_fetch = datetime.now()
        
        # Has data if ticker has segments or static has data
        return len(self.ticker_segments) > 0 or self.static_data is not None
    
    def has_data(self) -> bool:
        """Check if we have ticker or static data."""
        if self.layout == 'single':
            return len(self.segments) > 0
        else:
            # Multi-panel: has data if ticker or static has content
            return len(self.ticker_segments) > 0 or self.static_data is not None
    
    def should_fetch(self, now: datetime) -> bool:
        """Refresh ticker data periodically."""
        if self.last_fetch is None:
            return True
        return (now - self.last_fetch).total_seconds() >= self.refresh_interval
    
    def should_render(self, now: datetime) -> bool:
        """Re-render when data changes or on first render."""
        if self.last_render is None:
            return True
        # Only re-render when data changes (fetched new segments)
        return self.last_fetch and self.last_fetch > self.last_render
    
    async def render(self, width: int, height: int) -> Optional[Image.Image]:
        """
        Render ticker segments into frames.
        
        For single mode: Returns first frame, stores all in self.frames
        For multi mode: Returns composite first frame, stores panel frames separately
        """
        if self.layout == 'single':
            return await self._render_single_mode(width, height)
        else:
            return await self._render_multi_panel_mode(width, height)
    
    async def _render_single_mode(self, width: int, height: int):
        """Render single ticker across full display."""
        if not self.segments:
            return None
        
        # Create ticker frames for full display
        self.frames = self._create_ticker_frames_single(width, height)
        
        if self.frames:
            return self.frames[0]
        return None
    
    async def _render_multi_panel_mode(self, width: int, height: int):
        """Render ticker GIF + static panel image."""
        panel_height = height // 2  # Assume 2 panels
        
        # Render ticker panel
        if self.ticker_segments:
            self.ticker_frames = self._create_ticker_frames_for_segments(
                self.ticker_segments, width, panel_height
            )
            self.ticker_gif = self.frames_to_gif_bytes(self.ticker_frames, fps=30)
            logger.info(f"Ticker GIF: {len(self.ticker_gif)/1024:.1f} KB, {len(self.ticker_frames)} frames")
        
        # Render static panel
        if self.static_data:
            self.static_image = await self._render_static_panel(width, panel_height)
            logger.info(f"Static panel: {self.static_mode} display")
        
        # Return composite initial frame for display
        if self.ticker_frames or self.static_image:
            composite = Image.new('RGB', (width, height), color=(0, 0, 0))
            
            # Place ticker panel
            if self.ticker_frames:
                if self.ticker_panel_idx == 0:
                    composite.paste(self.ticker_frames[0], (0, 0))
                else:
                    composite.paste(self.ticker_frames[0], (0, panel_height))
            
            # Place static panel
            if self.static_image:
                if self.static_panel_idx == 0:
                    composite.paste(self.static_image, (0, 0))
                else:
                    composite.paste(self.static_image, (0, panel_height))
            
            return composite
        
        return None
    
    async def _render_static_panel(self, width: int, height: int):
        """
        Render static panel content as multiple "pages" to cycle through.
        For stocks: Show 2 stocks per page for readability.
        """
        self.static_images = []
        
        if self.static_mode == 'stocks':
            # Show 2 stocks per page for better readability
            items_per_page = 2
            stocks = self.static_data
            
            # Create pages
            for i in range(0, len(stocks), items_per_page):
                page_stocks = stocks[i:i + items_per_page]
                page_image = self._render_stocks_page(page_stocks, width, height)
                self.static_images.append(page_image)
            
            logger.info(f"Created {len(self.static_images)} stock pages ({items_per_page} stocks each)")
        
        elif self.static_mode == 'sports':
            # Show 2 games per page
            items_per_page = 2
            games = self.static_data
            
            for i in range(0, len(games), items_per_page):
                page_games = games[i:i + items_per_page]
                page_image = self._render_sports_page(page_games, width, height)
                self.static_images.append(page_image)
            
            logger.info(f"Created {len(self.static_images)} sports pages ({items_per_page} games each)")
        
        elif self.static_mode == 'weather':
            from core.rendering import render_weather
            page = render_weather(
                self.static_data['current'],
                self.static_data['forecast'],
                width=width,
                height=height
            )
            self.static_images = [page]
        
        elif self.static_mode == 'clock':
            from core.rendering import render_clock_with_weather_split
            from core.data import fetch_current_weather, fetch_daily_forecast
            from config import CLOCK_THEME, CLOCK_24H
            
            # Fetch weather for clock
            weather = await fetch_current_weather()
            forecast = await fetch_daily_forecast()
            
            page = render_clock_with_weather_split(
                weather, forecast,
                total_width=width,
                total_height=height,
                theme=CLOCK_THEME,
                hour24=CLOCK_24H
            )
            self.static_images = [page]
        
        # Return first page
        return self.static_images[0] if self.static_images else None
    
    def _render_stocks_page(self, stocks, width, height):
        """Render a page showing 2 stocks with large, readable text (symbol + % only)."""
        from PIL import Image, ImageDraw, ImageFont
        from core.rendering.stocks_display_png import format_percentage_change
        
        img = Image.new('RGB', (width, height), color=(0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("./fonts/PixelOperator.ttf", 12)
        except:
            font = ImageFont.load_default()
        
        # Show 2 stocks vertically (10px each)
        for idx, stock in enumerate(stocks[:2]):
            y_offset = idx * 10
            symbol = stock['symbol']
            change_pct = stock['change_percent']
            is_up = stock['is_up']
            
            color = (100, 255, 100) if is_up else (255, 100, 100)
            arrow = "▲" if is_up else "▼"
            
            # Symbol on left (white)
            draw.text((2, y_offset - 1), symbol, fill=(255, 255, 255), font=font)
            
            # Change percentage on right (colored)
            change_text = format_percentage_change(arrow, change_pct)
            text_bbox = draw.textbbox((0, 0), change_text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            change_x = width - text_width - 2
            draw.text((change_x, y_offset - 1), change_text, fill=color, font=font)
        
        return img
    
    def _render_sports_page(self, games, width, height):
        """Render a page showing 2 games."""
        from core.rendering import render_upcoming_games
        # Use existing renderer (it handles 2 games well)
        return render_upcoming_games(games, width=width, height=height)
    
    def has_priority(self) -> bool:
        """Ticker never has priority."""
        return False
    
    def get_frames(self) -> List[Image.Image]:
        """Get ticker animation frames for playback."""
        if self.layout == 'single':
            return self.frames
        else:
            # Return None for multi-panel - use get_panel_frames() instead
            return None
    
    def get_panel_frames(self) -> List[List[Image.Image]]:
        """Get per-panel ticker frames for multi-panel playback."""
        return self.panel_frames
    
    def frames_to_gif_bytes(self, frames: List[Image.Image], fps: int = 30) -> bytes:
        """
        Convert frames to GIF bytes for smoother playback.
        
        Args:
            frames: List of PIL Images
            fps: Target frames per second
        
        Returns:
            GIF bytes ready for upload
        """
        if not frames:
            return None
        
        import io
        
        gif_buffer = io.BytesIO()
        frame_duration_ms = int(1000 / fps)
        
        # Save as GIF
        frames[0].save(
            gif_buffer,
            format='GIF',
            save_all=True,
            append_images=frames[1:],
            duration=frame_duration_ms,
            loop=0  # Loop forever
        )
        
        return gif_buffer.getvalue()
    
    def get_gif_bytes(self) -> bytes:
        """Get single-mode ticker as GIF bytes."""
        if self.layout == 'single' and self.frames:
            return self.frames_to_gif_bytes(self.frames, fps=30)
        return None
    
    def get_panel_gifs(self) -> List[bytes]:
        """Get multi-panel tickers as GIF bytes (one per panel)."""
        if self.layout == 'multi' and self.panel_frames:
            return [
                self.frames_to_gif_bytes(frames, fps=30) 
                for frames in self.panel_frames
            ]
        return []
    
    def get_ticker_gif_with_panel(self):
        """Get ticker GIF and which panel to upload it to."""
        if self.layout == 'multi' and self.ticker_gif:
            return (self.ticker_gif, self.ticker_panel_idx)
        return None
    
    def get_static_image_with_panel(self):
        """Get current static page and which panel to upload it to."""
        if self.layout == 'multi' and self.static_images:
            current_page = self.static_images[self.static_page_index]
            return (current_page, self.static_panel_idx)
        return None
    
    def get_static_page_count(self):
        """Get total number of static pages."""
        return len(self.static_images)
    
    def advance_static_page(self):
        """Advance to next static page (for cycling)."""
        if self.static_images:
            self.static_page_index = (self.static_page_index + 1) % len(self.static_images)
            logger.debug(f"Advanced to static page {self.static_page_index + 1}/{len(self.static_images)}")
    
    async def _fetch_sports_with_source(self, source, max_games):
        """Helper to fetch sports data from a given source."""
        try:
            games = []
            
            if source == 'my_teams':
                from core.data import fetch_upcoming_games
                games = await fetch_upcoming_games(today_only=False)
            elif source == 'all_live':
                from core.data.sports_data import fetch_all_live_games
                games = await fetch_all_live_games()
            elif source == 'all_upcoming':
                from core.data.sports_data import fetch_all_upcoming_games
                games = await fetch_all_upcoming_games()
            elif source == 'all':
                from core.data.sports_data import fetch_all_live_games, fetch_all_upcoming_games
                live = await fetch_all_live_games()
                upcoming = await fetch_all_upcoming_games()
                games = live + upcoming
            
            if not games:
                return None
            
            games = games[:max_games]
            logger.info(f"Sports data: {len(games)} games ({source})")
            
            return {
                'type': 'sports',
                'data': games,
                'render_func': self._render_sports_segment
            }
        except Exception as e:
            logger.warning(f"Error fetching sports: {e}")
            return None
    
    async def _fetch_sports_segment_ticker(self):
        """Fetch sports segment for ticker panel (uses ticker config)."""
        source = self.ticker_sports_source if self.layout == 'multi' else self.sports_source
        max_games = self.ticker_sports_max if self.layout == 'multi' else self.sports_max
        
        return await self._fetch_sports_with_source(source, max_games)
    
    async def _fetch_stocks_segment_ticker(self):
        """Fetch stocks segment for ticker panel (uses ticker config)."""
        source = self.ticker_stocks_source if self.layout == 'multi' else self.stocks_source
        max_symbols = self.ticker_stocks_max if self.layout == 'multi' else self.stocks_max
        
        return await self._fetch_stocks_with_source(source, max_symbols)
    
    async def _fetch_stocks_with_source(self, source, max_symbols):
        """Helper to fetch stocks data from a given source."""
        try:
            quotes = []
            
            if source == 'my_symbols':
                from core.data import fetch_stock_quotes
                quotes = await fetch_stock_quotes()
            elif source == 'gainers':
                from core.data.stocks_data import fetch_market_gainers
                quotes = await fetch_market_gainers(limit=max_symbols)
            elif source == 'losers':
                from core.data.stocks_data import fetch_market_losers
                quotes = await fetch_market_losers(limit=max_symbols)
            elif source == 'mixed':
                from core.data.stocks_data import fetch_market_mixed
                quotes = await fetch_market_mixed(limit=max_symbols)
            elif source == 'active':
                from core.data.stocks_data import fetch_market_active
                quotes = await fetch_market_active(limit=max_symbols)
            
            if not quotes:
                return None
            
            quotes = quotes[:max_symbols]
            logger.info(f"Stocks data: {len(quotes)} symbols ({source})")
            
            return {
                'type': 'stocks',
                'data': quotes,
                'render_func': self._render_stocks_segment
            }
        except Exception as e:
            logger.warning(f"Error fetching stocks: {e}")
            return None
    
    async def _fetch_static_panel_data(self):
        """Fetch data for static panel based on configured mode."""
        try:
            if self.static_mode == 'sports':
                games = []
                result = await self._fetch_sports_with_source(
                    self.static_sports_source,
                    self.static_sports_max
                )
                return result['data'] if result else None
            
            elif self.static_mode == 'stocks':
                result = await self._fetch_stocks_with_source(
                    self.static_stocks_source,
                    self.static_stocks_max
                )
                return result['data'] if result else None
            
            elif self.static_mode == 'weather':
                from core.data import fetch_current_weather, fetch_daily_forecast
                weather = await fetch_current_weather()
                forecast = await fetch_daily_forecast()
                return {'current': weather, 'forecast': forecast}
            
            elif self.static_mode == 'clock':
                # Clock doesn't need data (shows current time)
                return {'mode': 'clock'}
            
            return None
        except Exception as e:
            logger.warning(f"Error fetching static panel data: {e}")
            return None
    
    async def _fetch_sports_segment_single(self):
        """Fetch sports ticker segment based on configured source."""
        try:
            games = []
            
            # Fetch based on configured source
            if self.sports_source == 'my_teams':
                from core.data import fetch_upcoming_games
                games = await fetch_upcoming_games(today_only=False)
            elif self.sports_source == 'all_live':
                from core.data.sports_data import fetch_all_live_games
                games = await fetch_all_live_games()
            elif self.sports_source == 'all_upcoming':
                from core.data.sports_data import fetch_all_upcoming_games
                games = await fetch_all_upcoming_games()
            elif self.sports_source == 'all':
                from core.data.sports_data import fetch_all_live_games, fetch_all_upcoming_games
                live = await fetch_all_live_games()
                upcoming = await fetch_all_upcoming_games()
                games = live + upcoming
            
            if not games:
                return None
            
            # Limit to max_games
            games = games[:self.sports_max]
            
            logger.info(f"Ticker sports: {len(games)} games ({self.sports_source})")
            
            # Return segment info
            return {
                'type': 'sports',
                'data': games,
                'render_func': self._render_sports_segment
            }
        except Exception as e:
            logger.warning(f"Error fetching sports for ticker: {e}")
            return None
    
    async def _fetch_sports_segment_for_panel(self, panel_config):
        """Fetch sports segment for a specific panel configuration."""
        try:
            sports_config = panel_config.get('sports', {})
            source = sports_config.get('source', 'my_teams')
            max_games = sports_config.get('max_games', 10)
            
            games = []
            
            # Fetch based on source
            if source == 'my_teams':
                from core.data import fetch_upcoming_games
                games = await fetch_upcoming_games(today_only=False)
            elif source == 'all_live':
                from core.data.sports_data import fetch_all_live_games
                games = await fetch_all_live_games()
            elif source == 'all_upcoming':
                from core.data.sports_data import fetch_all_upcoming_games
                games = await fetch_all_upcoming_games()
            elif source == 'all':
                from core.data.sports_data import fetch_all_live_games, fetch_all_upcoming_games
                live = await fetch_all_live_games()
                upcoming = await fetch_all_upcoming_games()
                games = live + upcoming
            
            if not games:
                return None
            
            games = games[:max_games]
            logger.info(f"Panel sports: {len(games)} games ({source})")
            
            return {
                'type': 'sports',
                'data': games,
                'render_func': self._render_sports_segment
            }
        except Exception as e:
            logger.warning(f"Error fetching sports for panel: {e}")
            return None
    
    async def _fetch_stocks_segment_single(self):
        """Fetch stocks ticker segment based on configured source."""
        try:
            quotes = []
            
            # Fetch based on configured source
            if self.stocks_source == 'my_symbols':
                from core.data import fetch_stock_quotes
                quotes = await fetch_stock_quotes()
            elif self.stocks_source == 'gainers':
                from core.data.stocks_data import fetch_market_gainers
                quotes = await fetch_market_gainers(limit=self.stocks_max)
            elif self.stocks_source == 'losers':
                from core.data.stocks_data import fetch_market_losers
                quotes = await fetch_market_losers(limit=self.stocks_max)
            elif self.stocks_source == 'mixed':
                from core.data.stocks_data import fetch_market_mixed
                quotes = await fetch_market_mixed(limit=self.stocks_max)
            elif self.stocks_source == 'active':
                from core.data.stocks_data import fetch_market_active
                quotes = await fetch_market_active(limit=self.stocks_max)
            elif self.stocks_source == 'trending':
                # Placeholder - would need real API for trending
                from core.data import fetch_stock_quotes
                quotes = await fetch_stock_quotes()
                logger.info("'trending' source not yet implemented, using my_symbols")
            
            if not quotes:
                return None
            
            # Limit to max_symbols (if not already limited by fetch function)
            quotes = quotes[:self.stocks_max]
            
            logger.info(f"Ticker stocks: {len(quotes)} symbols ({self.stocks_source})")
            
            return {
                'type': 'stocks',
                'data': quotes,
                'render_func': self._render_stocks_segment
            }
        except Exception as e:
            logger.warning(f"Error fetching stocks for ticker: {e}")
            return None
    
    async def _fetch_stocks_segment_for_panel(self, panel_config):
        """Fetch stocks segment for a specific panel configuration."""
        try:
            stocks_config = panel_config.get('stocks', {})
            source = stocks_config.get('source', 'my_symbols')
            max_symbols = stocks_config.get('max_symbols', 10)
            
            quotes = []
            
            # Fetch based on source
            if source == 'my_symbols':
                from core.data import fetch_stock_quotes
                quotes = await fetch_stock_quotes()
            elif source == 'gainers':
                from core.data.stocks_data import fetch_market_gainers
                quotes = await fetch_market_gainers(limit=max_symbols)
            elif source == 'losers':
                from core.data.stocks_data import fetch_market_losers
                quotes = await fetch_market_losers(limit=max_symbols)
            elif source == 'mixed':
                from core.data.stocks_data import fetch_market_mixed
                quotes = await fetch_market_mixed(limit=max_symbols)
            elif source == 'active':
                from core.data.stocks_data import fetch_market_active
                quotes = await fetch_market_active(limit=max_symbols)
            
            if not quotes:
                return None
            
            quotes = quotes[:max_symbols]
            logger.info(f"Panel stocks: {len(quotes)} symbols ({source})")
            
            return {
                'type': 'stocks',
                'data': quotes,
                'render_func': self._render_stocks_segment
            }
        except Exception as e:
            logger.warning(f"Error fetching stocks for panel: {e}")
            return None
    
    async def _fetch_weather_segment(self):
        """Fetch weather ticker segment."""
        from core.data import fetch_daily_forecast
        
        try:
            forecast = await fetch_daily_forecast()
            if not forecast:
                return None
            
            return {
                'type': 'weather',
                'data': forecast,
                'render_func': self._render_weather_segment
            }
        except Exception as e:
            logger.warning(f"Error fetching weather for ticker: {e}")
            return None
    
    def _render_sports_segment(self, draw, x_offset, height, games):
        """
        Render sports segment with team colors and logos.
        
        Returns: width of rendered segment
        """
        from core.rendering.sports_display_png import (
            load_team_logo, get_league_letter, get_team_color
        )
        from PIL import ImageFont
        
        try:
            font = ImageFont.truetype("./fonts/PixelOperator.ttf", 12)  # Larger for readability
        except:
            font = ImageFont.load_default()
        
        current_x = x_offset
        
        for game in games:
            away = game['away']
            home = game['home']
            time_str = game.get('time', 'TBD')
            league = game.get('league', '')
            state = game.get('state', '')
            
            # Get team colors
            away_color = get_team_color(away, league, (200, 200, 200))
            home_color = get_team_color(home, league, (255, 255, 255))
            
            # League indicator
            league_letter = get_league_letter(league)
            y_center = height // 2 - 6  # Adjusted for larger font
            draw.text((current_x, y_center), f"[{league_letter}]", fill=(128, 128, 128), font=font)
            current_x += 20  # More space for larger text
            
            # Away team (in team color)
            draw.text((current_x, y_center), away, fill=away_color, font=font)
            text_bbox = draw.textbbox((current_x, 0), away, font=font)
            current_x = text_bbox[2] + 3
            
            # @ symbol
            draw.text((current_x, y_center), "@", fill=(100, 100, 100), font=font)
            current_x += 10
            
            # Home team (in team color)
            draw.text((current_x, y_center), home, fill=home_color, font=font)
            text_bbox = draw.textbbox((current_x, 0), home, font=font)
            current_x = text_bbox[2] + 5
            
            # Time/score
            from core.rendering.sports_display_png import format_game_time
            
            if state in ['inProgress', 'in']:
                # Live game - show scores in yellow
                score_text = f"{game.get('away_score', 0)}-{game.get('home_score', 0)}"
                period = game.get('period', '')
                if period:
                    score_text += f" {period}"
                draw.text((current_x, y_center), score_text, fill=(255, 255, 0), font=font)
                text_bbox = draw.textbbox((current_x, 0), score_text, font=font)
                current_x = text_bbox[2]
            else:
                # Upcoming game - show time in blue
                time_display = format_game_time(time_str, compact=True)
                draw.text((current_x, y_center), time_display, fill=(100, 200, 255), font=font)
                text_bbox = draw.textbbox((current_x, 0), time_display, font=font)
                current_x = text_bbox[2]
            
            current_x += 25  # More spacing for larger text
            
            # Add separator
            draw.text((current_x - 18, y_center), "|", fill=(100, 100, 100), font=font)
        
        return current_x - x_offset
    
    def _render_stocks_segment(self, draw, x_offset, height, quotes):
        """Render stocks segment with prices and changes."""
        from core.rendering.stocks_display_png import format_percentage_change
        from PIL import ImageFont
        
        try:
            font = ImageFont.truetype("./fonts/PixelOperator.ttf", 12)  # Larger for readability
        except:
            font = ImageFont.load_default()
        
        current_x = x_offset
        y_center = height // 2 - 6  # Adjusted for larger font
        
        for quote in quotes:
            symbol = quote['symbol']
            price = quote['price']
            change_pct = quote['change_percent']
            is_up = quote['is_up']
            
            # Color: green for up, red for down
            color = (100, 255, 100) if is_up else (255, 100, 100)
            arrow = "▲" if is_up else "▼"
            
            # Format: PLTR $25.30 ▲18%
            text = f"{symbol} ${price:.2f} "
            draw.text((current_x, y_center), text, fill=(255, 255, 255), font=font)
            
            text_bbox = draw.textbbox((current_x, 0), text, font=font)
            current_x = text_bbox[2]
            
            # Add change percentage in color
            change_text = format_percentage_change(arrow, change_pct)
            draw.text((current_x, y_center), change_text, fill=color, font=font)
            
            text_bbox = draw.textbbox((current_x, 0), change_text, font=font)
            current_x = text_bbox[2] + 25  # More spacing
            
            # Add separator
            draw.text((current_x - 18, y_center), "|", fill=(100, 100, 100), font=font)
        
        return current_x - x_offset
    
    def _render_weather_segment(self, draw, x_offset, height, forecast):
        """Render weather segment with forecast."""
        from PIL import ImageFont
        
        try:
            font = ImageFont.truetype("./fonts/PixelOperator.ttf", 12)  # Larger for readability
        except:
            font = ImageFont.load_default()
        
        current_x = x_offset
        y_center = height // 2 - 6  # Adjusted for larger font
        
        for day in forecast:
            day_name = day.get('day', '')[:3]  # Mon, Tue, etc.
            temp = day.get('temp', 0)
            condition = day.get('condition', '')[:10]
            
            text = f"{day_name}: {temp}°F {condition}"
            draw.text((current_x, y_center), text, fill=(100, 200, 255), font=font)
            
            text_bbox = draw.textbbox((current_x, 0), text, font=font)
            current_x = text_bbox[2] + 25
            
            # Add separator
            draw.text((current_x - 18, y_center), "|", fill=(100, 100, 100), font=font)
        
        return current_x - x_offset
    
    def _create_ticker_frames_single(self, width: int, height: int) -> List[Image.Image]:
        """Create scrolling animation frames from all segments."""
        from PIL import ImageDraw
        
        # Calculate total width needed
        # Create a temporary image to measure
        temp_img = Image.new('RGB', (2000, height), color=(0, 0, 0))
        temp_draw = ImageDraw.Draw(temp_img)
        
        current_x = width  # Start off-screen to the right
        
        # Render all segments to measure total width
        for segment in self.segments:
            segment_width = segment['render_func'](
                temp_draw, current_x, height, segment['data']
            )
            current_x += segment_width
        
        total_width = current_x
        
        # Now create the actual canvas with correct width
        canvas = Image.new('RGB', (total_width, height), color=(0, 0, 0))
        draw = ImageDraw.Draw(canvas)
        
        # Render all segments for real
        current_x = width
        for segment in self.segments:
            segment['render_func'](draw, current_x, height, segment['data'])
            current_x += segment['render_func'](draw, current_x, height, segment['data'])
        
        # Generate frames by sliding window
        frames = []
        for x_offset in range(0, total_width - width + 20, self.scroll_speed):
            frame = canvas.crop((x_offset, 0, x_offset + width, height))
            frames.append(frame)
        
        logger.info(f"Created {len(frames)} ticker frames ({total_width}px total)")
        return frames
    
    def _create_ticker_frames_for_segments(self, segments: list, width: int, height: int) -> List[Image.Image]:
        """
        Create ticker frames for a list of segments (used by multi-panel mode).
        
        Args:
            segments: List of segment dicts
            width: Panel width
            height: Panel height
        
        Returns:
            List of animation frames
        """
        from PIL import ImageDraw
        
        # Measure total width
        temp_img = Image.new('RGB', (2000, height), color=(0, 0, 0))
        temp_draw = ImageDraw.Draw(temp_img)
        
        current_x = width
        for segment in segments:
            segment_width = segment['render_func'](
                temp_draw, current_x, height, segment['data']
            )
            current_x += segment_width
        
        total_width = current_x
        
        # Create actual canvas
        canvas = Image.new('RGB', (total_width, height), color=(0, 0, 0))
        draw = ImageDraw.Draw(canvas)
        
        # Render segments
        current_x = width
        for segment in segments:
            segment['render_func'](draw, current_x, height, segment['data'])
            current_x += segment['render_func'](draw, current_x, height, segment['data'])
        
        # Generate frames
        frames = []
        for x_offset in range(0, total_width - width + 20, self.scroll_speed):
            frame = canvas.crop((x_offset, 0, x_offset + width, height))
            frames.append(frame)
        
        logger.debug(f"Created {len(frames)} frames for panel ticker ({total_width}px)")
        return frames

