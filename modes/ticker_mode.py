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
        self.ticker_modes = config.get('TICKER_MODES', ['sports', 'stocks'])
        self.scroll_speed = config.get('TICKER_SCROLL_SPEED', 3)
        self.refresh_interval = config.get('TICKER_REFRESH_INTERVAL', 30)
        self.height = config.get('TICKER_HEIGHT', 20)  # Which panel to use
        
        # Ticker-specific configs (loaded from config.yml if available)
        from config_loader import ConfigLoader
        cfg = ConfigLoader()
        self.sports_source = cfg.get_string('ticker.sports.source', 'my_teams')
        self.sports_max = cfg.get_int('ticker.sports.max_games', 10)
        self.stocks_source = cfg.get_string('ticker.stocks.source', 'my_symbols')
        self.stocks_max = cfg.get_int('ticker.stocks.max_symbols', 10)
        
        # Data from modes
        self.segments = []
        self.frames = []
    
    async def fetch_data(self) -> bool:
        """Fetch data for all ticker segments."""
        try:
            self.segments = []
            
            # Collect ticker segments from configured modes
            if 'sports' in self.ticker_modes:
                segment = await self._fetch_sports_segment()
                if segment:
                    self.segments.append(segment)
            
            if 'stocks' in self.ticker_modes:
                segment = await self._fetch_stocks_segment()
                if segment:
                    self.segments.append(segment)
            
            if 'weather' in self.ticker_modes:
                segment = await self._fetch_weather_segment()
                if segment:
                    self.segments.append(segment)
            
            self.last_fetch = datetime.now()
            return len(self.segments) > 0
        except Exception as e:
            logger.error(f"Error fetching ticker data: {e}")
            return False
    
    def has_data(self) -> bool:
        """Check if we have ticker segments."""
        return len(self.segments) > 0
    
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
        
        Note: This returns a SINGLE combined image of all segments.
        The frames are stored in self.frames for playback.
        """
        if not self.segments:
            return None
        
        # Composite all segments into one long ticker
        self.frames = self._create_ticker_frames(width, self.height)
        
        # Return the first frame for initial display
        if self.frames:
            return self.frames[0]
        return None
    
    def has_priority(self) -> bool:
        """Ticker never has priority."""
        return False
    
    def get_frames(self) -> List[Image.Image]:
        """Get ticker animation frames for playback."""
        return self.frames
    
    async def _fetch_sports_segment(self):
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
    
    async def _fetch_stocks_segment(self):
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
        Render sports segment with logos and game info.
        
        Returns: width of rendered segment
        """
        from core.rendering.sports_display_png import load_team_logo, get_league_letter
        from PIL import ImageFont
        
        try:
            font = ImageFont.truetype("./fonts/PixelOperator.ttf", 8)
        except:
            font = ImageFont.load_default()
        
        current_x = x_offset
        
        for game in games:
            away = game['away']
            home = game['home']
            time_str = game.get('time', 'TBD')
            league = game.get('league', '')
            
            # Away logo (8x8)
            away_logo = load_team_logo(away, league, max_size=(8, 8))
            if away_logo:
                # Note: Parent function will paste this
                pass
            
            # Render: 🏀 DET @ BOS 7PM
            league_letter = get_league_letter(league)
            
            # For now, just text - logos would need to be handled by parent
            text = f"[{league_letter}] {away} @ {home}"
            
            # Add time
            from core.rendering.sports_display_png import format_game_time
            time_display = format_game_time(time_str, compact=True)
            text += f" {time_display}"
            
            # Draw text
            draw.text((current_x, height // 2 - 4), text, fill=(255, 200, 200), font=font)
            
            # Calculate width
            text_bbox = draw.textbbox((current_x, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            current_x += text_width + 20  # Add spacing
            
            # Add separator
            draw.text((current_x - 15, height // 2 - 4), "|", fill=(100, 100, 100), font=font)
        
        return current_x - x_offset
    
    def _render_stocks_segment(self, draw, x_offset, height, quotes):
        """Render stocks segment with prices and changes."""
        from core.rendering.stocks_display_png import format_percentage_change
        from PIL import ImageFont
        
        try:
            font = ImageFont.truetype("./fonts/PixelOperator.ttf", 8)
        except:
            font = ImageFont.load_default()
        
        current_x = x_offset
        
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
            draw.text((current_x, height // 2 - 4), text, fill=(255, 255, 255), font=font)
            
            text_bbox = draw.textbbox((current_x, 0), text, font=font)
            current_x = text_bbox[2]
            
            # Add change percentage in color
            change_text = format_percentage_change(arrow, change_pct)
            draw.text((current_x, height // 2 - 4), change_text, fill=color, font=font)
            
            text_bbox = draw.textbbox((current_x, 0), change_text, font=font)
            current_x = text_bbox[2] + 20
            
            # Add separator
            draw.text((current_x - 15, height // 2 - 4), "|", fill=(100, 100, 100), font=font)
        
        return current_x - x_offset
    
    def _render_weather_segment(self, draw, x_offset, height, forecast):
        """Render weather segment with forecast."""
        from PIL import ImageFont
        
        try:
            font = ImageFont.truetype("./fonts/PixelOperator.ttf", 8)
        except:
            font = ImageFont.load_default()
        
        current_x = x_offset
        
        for day in forecast:
            day_name = day.get('day', '')[:3]  # Mon, Tue, etc.
            temp = day.get('temp', 0)
            condition = day.get('condition', '')[:10]
            
            text = f"{day_name}: {temp}°F {condition}"
            draw.text((current_x, height // 2 - 4), text, fill=(100, 200, 255), font=font)
            
            text_bbox = draw.textbbox((current_x, 0), text, font=font)
            current_x = text_bbox[2] + 20
            
            # Add separator
            draw.text((current_x - 15, height // 2 - 4), "|", fill=(100, 100, 100), font=font)
        
        return current_x - x_offset
    
    def _create_ticker_frames(self, width: int, height: int) -> List[Image.Image]:
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

