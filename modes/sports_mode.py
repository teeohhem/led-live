"""
Sports mode - displays live games and upcoming games.
"""
from datetime import datetime
from typing import Optional
from PIL import Image
import logging

from .base_mode import BaseMode
from core.data import fetch_all_games, fetch_upcoming_games
from core.rendering import render_scoreboard, render_upcoming_games

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
        
        # Cycle state for when priority is disabled
        self.sports_cycle_index = 0
        self.last_sports_cycle = datetime.now()
    
    async def fetch_data(self) -> bool:
        """Fetch game data from ESPN."""
        try:
            if 'live' in self.sports_modes and 'upcoming' in self.sports_modes:
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
        
        # Check if periodic refresh needed
        needs_refresh = (
            self.last_render is None or
            (now - self.last_render).total_seconds() >= self.refresh_interval
        )
        
        if data_changed:
            self.prev_snapshot = current_snapshot
            return True
        
        return needs_refresh
    
    async def render(self, width: int, height: int) -> Optional[Image.Image]:
        """Render the sports display."""
        if not self.display_games:
            return None
        
        logger.info(f"Rendering {self.display_type} sports ({len(self.display_games)} games)")
        
        if self.display_type == 'live':
            return render_scoreboard(self.display_games, width=width, height=height)
        else:  # upcoming
            return render_upcoming_games(self.display_games, width=width, height=height)
    
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
    
    def _prepare_display_games(self, now: datetime):
        """
        Determine which games to display (live vs upcoming).
        
        Behavior depends on priority setting:
        - If priority enabled: Always show live when available, else upcoming
        - If priority disabled: Cycle between live and upcoming (if both configured)
        """
        self.display_games = []
        self.display_type = None
        
        live_games = self._get_live_games() if 'live' in self.sports_modes else []
        upcoming_games = self._get_upcoming_games() if 'upcoming' in self.sports_modes else []
        
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

