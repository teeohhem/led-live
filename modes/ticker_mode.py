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
            # Multi-panel mode - load per-panel configs
            self.panel_configs = cfg.get('ticker.panels', [])
            if not self.panel_configs:
                # Fallback to single mode if no panel configs
                logger.warning("Multi-panel ticker requested but no panel configs found, using single mode")
                self.layout = 'single'
        
        # Fallback single-mode config
        if self.layout == 'single':
            self.ticker_modes = cfg.get_list('ticker.single.modes', ['sports', 'stocks'])
            self.sports_source = cfg.get_string('ticker.single.sports.source', 'my_teams')
            self.sports_max = cfg.get_int('ticker.single.sports.max_games', 10)
            self.stocks_source = cfg.get_string('ticker.single.stocks.source', 'my_symbols')
            self.stocks_max = cfg.get_int('ticker.single.stocks.max_symbols', 10)
        
        # Data storage
        self.segments = []  # For single mode
        self.panel_segments = []  # For multi mode (list of segment lists)
        self.frames = []  # For single mode
        self.panel_frames = []  # For multi mode (list of frame lists)
    
    async def fetch_data(self) -> bool:
        """Fetch data for all ticker segments (single or multi-panel)."""
        try:
            if self.layout == 'single':
                return await self._fetch_single_mode()
            else:
                return await self._fetch_multi_panel_mode()
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
    
    async def _fetch_multi_panel_mode(self):
        """Fetch data for multi-panel ticker (independent per panel)."""
        self.panel_segments = []
        
        # Fetch data for each panel configuration
        for panel_idx, panel_config in enumerate(self.panel_configs):
            panel_modes = panel_config.get('modes', [])
            segments = []
            
            logger.info(f"Fetching ticker data for panel {panel_idx}: {panel_modes}")
            
            # Fetch segments for this panel
            if 'sports' in panel_modes:
                segment = await self._fetch_sports_segment_for_panel(panel_config)
                if segment:
                    segments.append(segment)
            
            if 'stocks' in panel_modes:
                segment = await self._fetch_stocks_segment_for_panel(panel_config)
                if segment:
                    segments.append(segment)
            
            if 'weather' in panel_modes:
                segment = await self._fetch_weather_segment()
                if segment:
                    segments.append(segment)
            
            self.panel_segments.append(segments)
        
        self.last_fetch = datetime.now()
        # Has data if any panel has segments
        return any(len(segs) > 0 for segs in self.panel_segments)
    
    def has_data(self) -> bool:
        """Check if we have ticker segments."""
        if self.layout == 'single':
            return len(self.segments) > 0
        else:
            return any(len(segs) > 0 for segs in self.panel_segments)
    
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
        """Render independent tickers for each panel."""
        if not self.panel_segments:
            return None
        
        # Calculate height per panel
        panel_count = len(self.panel_segments)
        panel_height = height // panel_count
        
        # Create frames for each panel
        self.panel_frames = []
        for panel_idx, segments in enumerate(self.panel_segments):
            if segments:
                frames = self._create_ticker_frames_for_segments(segments, width, panel_height)
                self.panel_frames.append(frames)
            else:
                # Empty panel - create blank frames
                blank = Image.new('RGB', (width, panel_height), color=(0, 0, 0))
                self.panel_frames.append([blank])
        
        # Composite first frame from all panels for initial display
        if self.panel_frames:
            first_composite = Image.new('RGB', (width, height), color=(0, 0, 0))
            y_offset = 0
            for frames in self.panel_frames:
                first_composite.paste(frames[0], (0, y_offset))
                y_offset += panel_height
            return first_composite
        
        return None
    
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

