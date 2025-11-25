"""
Sports mode - displays live games and upcoming games.
"""
from datetime import datetime
from typing import Optional
from PIL import Image
import logging

from .base_mode import BaseMode
from core.data import fetch_all_games, fetch_upcoming_games, fetch_live_games_by_leagues
from core.layout import LayoutLoader
from core.rendering.templated_renderer import TemplatedSportsRenderer

logger = logging.getLogger(__name__)


class SportsMode(BaseMode):
    """
    Sports display mode.
    
    Shows live games with priority, falls back to upcoming games.
    """
    
    def __init__(self, config):
        super().__init__("sports", config)
        self.games = []
        self.display_games = []
        self.display_type = None  # 'live' or 'upcoming'
        self.prev_snapshot = None
        
        # Config
        self.check_interval = config.get('SPORTS_CHECK_INTERVAL', 10)
        self.refresh_interval = config.get('DISPLAY_SPORTS_REFRESH_INTERVAL', 2)
        self.sports_modes = config.get('SPORTS_MODES', ['live', 'upcoming'])
        self.enable_priority = config.get('DISPLAY_SPORTS_PRIORITY', True)
        self.live_games_source = config.get('SPORTS_LIVE_GAMES_SOURCE', 'my_teams')
        self.live_games_leagues = config.get('SPORTS_LIVE_GAMES_LEAGUES', [])
        self.show_logos = config.get('SPORTS_SHOW_LOGOS', True)
        
        # Cycle state for when priority is disabled
        self.sports_cycle_index = 0
        self.last_sports_cycle = datetime.now()
        
        # Game cycling for all_leagues mode - rotate through games showing 2 at a time
        self.games_page_index = 0
        self.last_games_page_cycle = datetime.now()
        self.games_per_page = config.get('SPORTS_GAMES_PER_PAGE', 2)
        self.games_cycle_interval = config.get('SPORTS_GAMES_CYCLE_INTERVAL', 10)
        
        # Load layout template (required)
        try:
            from config import get_all_config
            config_dict = get_all_config()
            loader = LayoutLoader(config_dict)
            layout_template = loader.get_template('sports')
            # Override template's logo setting with config value
            layout_template.logo_enabled = self.show_logos
            self.layout_renderer = TemplatedSportsRenderer(layout_template)
            logger.info("Using templated sports renderer")
        except Exception as e:
            logger.error(f"Failed to load layout template: {e}")
            raise RuntimeError("Sports mode requires layout templates. Check core/layout/templates/")
    
    async def fetch_data(self) -> bool:
        """Fetch game data from ESPN."""
        try:
            # Check if we're using all_leagues mode for live games
            if self.live_games_source == 'all_leagues' and 'live' in self.sports_modes:
                if not self.live_games_leagues:
                    logger.warning("live_games_source is 'all_leagues' but no leagues specified. Please add 'live_games_leagues' to config.")
                    logger.warning("Example: live_games_leagues: ['NHL', 'NBA', 'NFL', 'MLB']")
                    self.games = []
                else:
                    # Fetch live games from specified leagues
                    live_games = await fetch_live_games_by_leagues(self.live_games_leagues)
                    
                    # If upcoming is also enabled, fetch those too (filtered by teams)
                    if 'upcoming' in self.sports_modes:
                        upcoming_games = await fetch_upcoming_games()
                        self.games = live_games + upcoming_games
                    else:
                        self.games = live_games
                    
                    logger.info(f"Fetched {len(self.games)} games (all_leagues mode)")
            elif 'live' in self.sports_modes or 'upcoming' in self.sports_modes:
                # Original behavior: fetch games filtered by teams
                self.games = await fetch_all_games()
                logger.info(f"Fetched {len(self.games)} games")
            else:
                self.games = []
            
            self.last_fetch = datetime.now()
            return True
        except Exception as e:
            logger.error(f"Error fetching sports data: {e}")
            return False
    
    def has_data(self) -> bool:
        """Check if we have games to display."""
        self._prepare_display_games(datetime.now())
        return len(self.display_games) > 0
    
    def should_fetch(self, now: datetime) -> bool:
        """Check if we need to fetch new game data."""
        if self.last_fetch is None:
            return True
        return (now - self.last_fetch).total_seconds() >= self.check_interval
    
    def should_render(self, now: datetime) -> bool:
        """Check if we need to re-render."""
        # Check if data changed
        current_snapshot = self._create_snapshot()
        data_changed = current_snapshot != self.prev_snapshot
        
        # Check if we need to cycle to next page of games
        time_since_cycle = (now - self.last_games_page_cycle).total_seconds()
        should_cycle = (
            self.live_games_source == 'all_leagues' and 
            len(self.display_games) > self.games_per_page and
            time_since_cycle >= self.games_cycle_interval
        )
        
        # Check if periodic refresh needed
        needs_refresh = (
            self.last_render is None or
            (now - self.last_render).total_seconds() >= self.refresh_interval
        )
        
        if data_changed:
            self.prev_snapshot = current_snapshot
            return True
        
        return needs_refresh or should_cycle
    
    async def render(self, width: int, height: int) -> Optional[Image.Image]:
        """Render the sports display."""
        if not self.display_games:
            logger.debug("No display games to render")
            return None
        
        # Determine which games to show (cycle through if in all_leagues mode)
        games_to_render = self._get_games_page()
        
        logger.info(f"Rendering {self.display_type} sports ({len(games_to_render)} of {len(self.display_games)} games)")
        
        try:
            result = self.layout_renderer.render_games(games_to_render, display_type=self.display_type)
            if result is None:
                logger.warning("Renderer returned None")
            return result
        except Exception as e:
            logger.error(f"Error rendering sports display: {e}", exc_info=True)
            return None
    
    def has_priority(self) -> bool:
        """Check if live games should trigger priority mode."""
        if not self.enable_priority:
            return False
        
        # Priority if we have live games
        return self.display_type == 'live' and len(self.display_games) > 0
    
    def _get_live_games(self):
        """Get only in-progress games."""
        return [
            g for g in self.games
            if g.get('state') in ['inProgress', 'in']
        ]
    
    def _get_upcoming_games(self):
        """Get only upcoming/scheduled games."""
        return [
            g for g in self.games
            if g.get('state') in ['pre', 'STATUS_SCHEDULED']
        ]
    
    def _get_games_page(self):
        """
        Get the current page of games to display.
        
        In all_leagues mode with many games, cycles through showing games_per_page at a time.
        In my_teams mode, shows all games (up to renderer's limit).
        """
        # If not using all_leagues mode, or few games, show all
        if self.live_games_source != 'all_leagues' or len(self.display_games) <= self.games_per_page:
            return self.display_games
        
        # Cycle through games
        now = datetime.now()
        time_since_cycle = (now - self.last_games_page_cycle).total_seconds()
        
        # Cycle based on configured interval
        if time_since_cycle >= self.games_cycle_interval:
            total_games = len(self.display_games)
            total_pages = (total_games + self.games_per_page - 1) // self.games_per_page  # Ceiling division
            self.games_page_index = (self.games_page_index + 1) % total_pages
            self.last_games_page_cycle = now
            logger.info(f"Cycling to games page {self.games_page_index + 1}/{total_pages}")
        
        # Get the current page slice
        start_idx = self.games_page_index * self.games_per_page
        end_idx = start_idx + self.games_per_page
        return self.display_games[start_idx:end_idx]
    
    def _prepare_display_games(self, now: datetime):
        """
        Determine which games to display (live vs upcoming).
        
        Behavior depends on priority setting:
        - If priority enabled: Always show live when available, else upcoming
        - If priority disabled: Cycle between live and upcoming (if both configured)
        """
        self.display_games = []
        self.display_type = None
        
        logger.debug(f"Preparing display games. Total games in memory: {len(self.games)}")
        
        live_games = self._get_live_games() if 'live' in self.sports_modes else []
        upcoming_games = self._get_upcoming_games() if 'upcoming' in self.sports_modes else []
        
        logger.debug(f"Found {len(live_games)} live games, {len(upcoming_games)} upcoming games")
        
        # If priority enabled, always show live when available
        if self.enable_priority:
            if live_games:
                self.display_games = live_games
                self.display_type = 'live'
            elif upcoming_games:
                self.display_games = upcoming_games
                self.display_type = 'upcoming'
        else:
            # Priority disabled - cycle between live and upcoming
            # If both modes are configured, alternate between them
            available_modes = []
            if live_games:
                available_modes.append(('live', live_games))
            if upcoming_games:
                available_modes.append(('upcoming', upcoming_games))
            
            if not available_modes:
                return  # No games at all
            
            # If only one type available, show it
            if len(available_modes) == 1:
                self.display_type, self.display_games = available_modes[0]
                return
            
            # Both types available - cycle between them
            # Check if it's time to switch (every 30 seconds)
            time_since_cycle = (now - self.last_sports_cycle).total_seconds()
            if time_since_cycle >= 30:  # Cycle every 30 seconds
                self.sports_cycle_index = (self.sports_cycle_index + 1) % len(available_modes)
                self.last_sports_cycle = now
                logger.info(f"Cycling sports sub-mode")
            
            self.display_type, self.display_games = available_modes[self.sports_cycle_index]
    
    def _create_snapshot(self):
        """Create a snapshot of current display state for change detection."""
        if not self.display_games:
            return None
        
        if self.display_type == 'live':
            return [
                (g['home'], g['away'], g.get('home_score'), g.get('away_score'),
                 g.get('period'), g.get('clock'), g.get('state'))
                for g in self.display_games
            ]
        else:  # upcoming
            return [
                (g['home'], g['away'], g.get('time'), g.get('state'))
                for g in self.display_games
            ]

