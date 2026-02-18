"""
Sports component for displaying live games.
"""

from typing import Optional, Any, List, Dict
from PIL import Image
from .base import Component


class SportsLiveComponent(Component):
    """
    Displays live or upcoming sports games.
    
    Config options:
        - leagues: List of leagues to show (default: all configured)
        - states: Game states to show (default: ['LIVE', 'UPCOMING'])
        - max_games: Maximum games to display (default: based on height)
        - filter_teams: Only show games with these teams
    """
    
    async def fetch_data(self) -> Optional[List[Dict[str, Any]]]:
        """Fetch sports game data."""
        from core.data import sports_fetcher, GameState
        
        try:
            leagues = self.config.get('leagues', None)  # None = all
            states_str = self.config.get('states', ['LIVE', 'UPCOMING'])
            
            # Convert string states to enum
            states = [GameState[s] for s in states_str if hasattr(GameState, s)]
            
            filter_teams = self.config.get('filter_teams', None)
            
            games = await sports_fetcher.fetch_games(
                leagues=leagues,
                states=states,
                filter_teams=filter_teams
            )
            
            # Limit to max_games
            max_games = self.config.get('max_games', None)
            if max_games and games:
                games = games[:max_games]
            
            return games
        except Exception as e:
            self.logger.error(f"Failed to fetch sports: {e}")
            return None
    
    def render(self, data: Optional[List[Dict[str, Any]]] = None) -> Image.Image:
        """
        Render sports games.
        
        Args:
            data: List of game dicts from fetch_data()
        
        Returns:
            PIL Image
        """
        from core.rendering.templated_renderer import TemplatedSportsRenderer
        from core.layout.loader import LayoutLoader
        from config import get_all_config
        
        # Load sports template for this size
        config_dict = get_all_config()
        loader = LayoutLoader(config_dict)
        
        # Get template matching our dimensions
        layout = loader.get_layout_for_dimensions(self.width, self.height)
        renderer = TemplatedSportsRenderer(layout)
        
        display_type = self.config.get('display_type', 'live')
        return renderer.render_games(data or [], display_type=display_type)


