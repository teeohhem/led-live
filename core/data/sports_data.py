"""
Sports data fetching from ESPN APIs.

Refactored to use base fetcher class and consolidate duplicate functions.

Key improvements:
- Single fetch_games() method replaces 4 duplicate functions
- Automatic retry logic via base class
- Better caching with configurable TTL
- Type-safe interfaces
- Reduced code duplication by ~150 lines
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

from .base_fetcher import DataFetcher

logger = logging.getLogger(__name__)

# Import configuration (loaded at startup via config.py)
from config import (
    SPORTS_TEST_MODE as TEST_MODE_RANDOM_2,
    SPORTS_NHL_TEAMS as TEAMS_NHL,
    SPORTS_NBA_TEAMS as TEAMS_NBA,
    SPORTS_NFL_TEAMS as TEAMS_NFL,
    SPORTS_MLB_TEAMS as TEAMS_MLB,
)


# ============================================================================
# Constants and Configuration
# ============================================================================

class League(str, Enum):
    """Supported sports leagues."""
    NHL = "NHL"
    NBA = "NBA"
    NFL = "NFL"
    MLB = "MLB"


class GameState(str, Enum):
    """Game states."""
    LIVE = "live"
    UPCOMING = "upcoming"
    COMPLETED = "completed"


# API Endpoints
API_ENDPOINTS = {
    League.NHL: "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard",
    League.NBA: "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard",
    League.NFL: "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard",
    League.MLB: "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard",
}

# Team configurations
LEAGUE_TEAMS = {
    League.NHL: TEAMS_NHL,
    League.NBA: TEAMS_NBA,
    League.NFL: TEAMS_NFL,
    League.MLB: TEAMS_MLB,
}

# League abbreviations
LEAGUE_LETTERS = {
    League.NHL: "H",  # Hockey
    League.NBA: "B",  # Basketball
    League.NFL: "F",  # Football
    League.MLB: "B",  # Baseball
}


def get_teams_for_league(league: str) -> List[str]:
    """
    Get the team list for a specific league.
    
    Args:
        league: League name (NHL, NBA, NFL, MLB)
        
    Returns:
        List of team abbreviations
    """
    try:
        league_enum = League(league.upper())
        return LEAGUE_TEAMS.get(league_enum, [])
    except ValueError:
        return []


def get_league_letter(league: str) -> str:
    """
    Convert league name to single letter.
    
    Args:
        league: League name
        
    Returns:
        Single letter abbreviation
    """
    try:
        league_enum = League(league.upper())
        return LEAGUE_LETTERS.get(league_enum, league[:1] if league else "")
    except ValueError:
        return league[:1] if league else ""


# ============================================================================
# Sports Data Fetcher
# ============================================================================

class SportsFetcher(DataFetcher[List[Dict[str, Any]]]):
    """
    Fetcher for ESPN sports data with filtering and caching.
    
    Consolidates multiple fetch functions into a single flexible interface.
    """
    
    def __init__(self, cache_ttl: int = 60):
        """
        Initialize sports fetcher.
        
        Args:
            cache_ttl: Cache time-to-live in seconds (default: 60)
        """
        super().__init__(cache_ttl=cache_ttl, logger_name='sports_fetcher')
    
    async def fetch(self) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch all games (implements abstract method).
        
        Returns:
            List of all games for configured teams
        """
        return await self.fetch_games(filter_teams=True)
    
    async def fetch_games(
        self,
        leagues: Optional[List[str]] = None,
        states: Optional[List[GameState]] = None,
        filter_teams: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Fetch games with flexible filtering.
        
        This single method replaces:
        - fetch_all_games()
        - fetch_all_live_games()
        - fetch_all_upcoming_games()
        - fetch_live_games_by_leagues()
        
        Args:
            leagues: List of leagues to fetch (None = all leagues)
            states: List of game states to include (None = all states)
            filter_teams: If True, only return games for configured teams
            
        Returns:
            List of game dicts matching the filters
        """
        # Determine which leagues to fetch
        if leagues:
            league_enums = [League(l.upper()) for l in leagues]
            endpoints = {l: API_ENDPOINTS[l] for l in league_enums}
        else:
            endpoints = API_ENDPOINTS.copy()
        
        # Fetch from all requested leagues
        all_games = []
        for league, url in endpoints.items():
            games = await self._fetch_from_endpoint(url, league, filter_teams)
            all_games.extend(games)
        
        # Filter by state if specified
        if states:
            state_values = [s.value if isinstance(s, GameState) else s for s in states]
            all_games = [
                game for game in all_games 
                if self._get_game_state(game) in state_values
            ]
        
        log_msg = f"Fetched {len(all_games)} games"
        if leagues:
            log_msg += f" from {', '.join([str(l) for l in leagues])}"
        if states:
            log_msg += f" (states: {', '.join([str(s) for s in states])})"
        if filter_teams:
            log_msg += " (filtered for your teams)"
        
        self.logger.info(log_msg)
        return all_games
    
    async def _fetch_from_endpoint(
        self, 
        url: str, 
        league: League,
        filter_teams: bool
    ) -> List[Dict[str, Any]]:
        """
        Fetch games from a single ESPN endpoint.
        
        Args:
            url: ESPN API endpoint URL
            league: League enum
            filter_teams: Whether to filter for configured teams
            
        Returns:
            List of game dicts from this league
        """
        data = await self.fetch_with_retry(url)
        
        if not data:
            return []
        
        games = []
        events = data.get("events", [])
        total_found = len(events)
        
        self.logger.debug(f"Found {total_found} total games in {league.value} scoreboard")
        
        for event in events:
            try:
                game = self._parse_game(event, league)
                
                # Filter for configured teams if requested
                if filter_teams:
                    if not self._should_include_game(game, league):
                        continue
                
                games.append(game)
                
            except Exception as e:
                short_name = event.get("shortName", "unknown")
                self.logger.error(f"Error parsing game {short_name}: {e}")
                continue
        
        if filter_teams:
            kept = len(games)
            if TEST_MODE_RANDOM_2:
                self.logger.info(f"Kept {kept} games (TEST MODE - all included)")
            else:
                self.logger.info(f"Kept {kept}/{total_found} games for your teams")
        else:
            self.logger.debug(f"Fetched {len(games)} games from {league.value}")
        
        return games
    
    @staticmethod
    def _parse_game(event: Dict[str, Any], league: League) -> Dict[str, Any]:
        """
        Parse ESPN game event into our format.
        
        Args:
            event: Raw ESPN event dict
            league: League enum
            
        Returns:
            Parsed game dict
        """
        short_name = event.get("shortName", "")
        
        # Extract competition data
        comp = event.get("competitions", [{}])[0]
        competitors = comp.get("competitors", [])
        
        # Parse teams and scores
        home_score = 0
        away_score = 0
        home_abbr = "???"
        away_abbr = "???"
        
        for c in competitors:
            score_val = c.get("score", "0")
            score = int(score_val) if score_val else 0
            
            if c.get("homeAway") == "home":
                home_score = score
                home_abbr = c.get("team", {}).get("abbreviation", "???")
            elif c.get("homeAway") == "away":
                away_score = score
                away_abbr = c.get("team", {}).get("abbreviation", "???")
        
        # Parse from short_name if not found in competitors
        if " @ " in short_name:
            away_abbr, home_abbr = short_name.split(" @ ")
        elif " VS " in short_name:
            away_abbr, home_abbr = short_name.split(" VS ")
        
        # Parse status
        status = comp.get("status", {})
        state = status.get("type", {}).get("state", "")
        clock = status.get("displayClock", "0:00")
        period_raw = status.get("period", "NO_PERIOD")
        time_detail = status.get("type", {}).get("detail", "")
        
        # Format period by league
        period = SportsFetcher._format_period(period_raw, league)
        
        # Extract outs and batting half for MLB
        situation = comp.get("situation", {})
        outs = None
        batting_half = None
        if league == League.MLB:
            outs = situation.get("outs")
            detail_lower = time_detail.lower()
            if detail_lower.startswith("top"):
                batting_half = "top"   # away team batting
                period = f"T {period}"
            elif detail_lower.startswith("bot"):
                batting_half = "bot"   # home team batting
                period = f"B {period}"
        
        return {
            "home": home_abbr,
            "away": away_abbr,
            "home_score": home_score,
            "away_score": away_score,
            "clock": clock,
            "period": period,
            "state": state,
            "league": league.value,
            "time": time_detail,
            "outs": outs,
            "batting_half": batting_half
        }
    
    @staticmethod
    def _format_period(period_raw: Any, league: League) -> str:
        """
        Format period/inning based on league.
        
        Args:
            period_raw: Raw period value from API
            league: League enum
            
        Returns:
            Formatted period string
        """
        try:
            period_num = int(period_raw) if period_raw != "NO_PERIOD" else 0
            
            if period_num <= 0:
                return ""
            
            if league == League.NBA or league == League.NFL:
                return f"Q{period_num}"
            elif league == League.NHL:
                return f"P{period_num}"
            elif league == League.MLB:
                if period_num >= 10:
                    return str(period_num)   # "10", "11", etc. — no suffix to keep it compact
                suffix = {1: "st", 2: "nd", 3: "rd"}.get(period_num, "th")
                return f"{period_num} {suffix}"
            else:
                return str(period_num)
                
        except (ValueError, TypeError):
            return ""
    
    @staticmethod
    def _should_include_game(game: Dict[str, Any], league: League) -> bool:
        """
        Check if game should be included based on team configuration.
        
        Args:
            game: Parsed game dict
            league: League enum
            
        Returns:
            True if game should be included
        """
        # Test mode includes all games
        if TEST_MODE_RANDOM_2:
            return True
        
        # Get configured teams for this league
        league_teams = LEAGUE_TEAMS.get(league, [])
        
        if not league_teams:
            return False
        
        # Check if either team is in our list
        home = game["home"].upper()
        away = game["away"].upper()
        
        return any(
            team.upper() in home or team.upper() in away
            for team in league_teams
        )
    
    @staticmethod
    def _get_game_state(game: Dict[str, Any]) -> str:
        """
        Determine game state from game dict.
        
        Args:
            game: Game dict
            
        Returns:
            State string: "live", "upcoming", or "completed"
        """
        state = game.get("state", "")
        
        if state in ["inProgress", "in"]:
            return GameState.LIVE.value
        elif state in ["pre", "STATUS_SCHEDULED"]:
            return GameState.UPCOMING.value
        elif state in ["post", "final"]:
            return GameState.COMPLETED.value
        else:
            return "unknown"


# ============================================================================
# Module-level API - use SportsFetcher class directly
# ============================================================================

# For convenience, create module-level fetcher instance
sports_fetcher = SportsFetcher(cache_ttl=60)
