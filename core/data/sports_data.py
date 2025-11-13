"""
Sports data fetching from ESPN APIs
"""
import httpx
import os
from pathlib import Path
from datetime import datetime, timedelta
import logging
logger = logging.getLogger(__name__)

# Import configuration (loaded at startup via config.py)
from config import (
    SPORTS_TEST_MODE as TEST_MODE_RANDOM_2,
    SPORTS_NHL_TEAMS as TEAMS_NHL,
    SPORTS_NBA_TEAMS as TEAMS_NBA,
    SPORTS_NFL_TEAMS as TEAMS_NFL,
    SPORTS_MLB_TEAMS as TEAMS_MLB,
)

# In-memory cache for game data
_games_cache = {
    'data': None,          # Cached game data
    'timestamp': None,     # When cache was last updated
    'ttl': 60              # Cache time-to-live in seconds
}


def get_teams_for_league(league):
    """Get the team list for a specific league"""
    league_map = {
        "NHL": TEAMS_NHL,
        "NBA": TEAMS_NBA,
        "NFL": TEAMS_NFL,
        "MLB": TEAMS_MLB,
    }
    return league_map.get(league, [])

# --- Sports API settings ---
API_ENDPOINTS = [
    "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard",
    "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard",
    "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard",
    "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"
]

# --- League abbreviations ---
def get_league_letter(league):
    """Convert league name to single letter"""
    league_map = {
        "NHL": "H",  # Hockey
        "NBA": "B",  # Basketball
        "NFL": "F",  # Football
        "MLB": "B",  # Baseball
    }
    return league_map.get(league, league[:1] if league else "")


# --- Fetch games from ESPN ---
async def fetch_games_from_endpoint(url, filter_teams=True):
    """
    Fetch games from ESPN endpoint.
    
    Args:
        url: ESPN API endpoint URL
        filter_teams: If True, filter for configured teams. If False, return all games.
    
    Returns:
        List of game dicts
    """
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url)
            data = resp.json()
        except Exception:
            return []

    games = []
    next_events = data.get("events", [])
    total_games_found = len(next_events)
    league = url.split('/')[-2].upper()
    logger.debug(f"Found {total_games_found} total games in {league} scoreboard")

    for game in next_events:
        try:
            short_name = game.get("shortName", "")
            home_score = 0
            away_score = 0
            
            comps = game.get("competitions", [])
            if not comps:
                continue
            
            comp = comps[0]
            competitors = comp.get("competitors", [])
            
            for c in competitors:
                score_val = c.get("score", "0")
                if c.get("homeAway") == "home":
                    home_score = int(score_val) if score_val else 0
                    home_abbr = c.get("team", {}).get("abbreviation", "???")
                elif c.get("homeAway") == "away":
                    away_score = int(score_val) if score_val else 0
                    away_abbr = c.get("team", {}).get("abbreviation", "???")
            
            status = comp.get("status", {})
            state = status.get("type", {}).get("state", "")
            status_name = status.get("type", {}).get("name", "")
            
            clock = status.get("displayClock", "0:00")
            period_raw = status.get("period", "NO_PERIOD")
            
            # Convert period to readable format
            try:
                period_num = int(period_raw) if period_raw != "NO_PERIOD" else 0
                if league == "NBA":
                    period = "Q" + str(period_num) if period_num > 0 else ""
                elif league == "NHL":
                    period = "P" + str(period_num) if period_num > 0 else ""
                elif league == "NFL":
                    period = "Q" + str(period_num) if period_num > 0 else ""
                elif league == "MLB":
                    period = "I" + str(period_num) if period_num > 0 else ""
                else:
                    period = str(period_num) if period_num > 0 else ""
            except:
                period = ""
            
            is_completed = state in ["post", "final"]
            period_num = int(period_raw) if period_raw != "NO_PERIOD" else 0
            is_live = (
                state == "inProgress" or
                state == "in" or
                (period_num > 0 and not is_completed)
            )
            
            # Parse team abbreviations
            if " @ " in short_name:
                away_abbr, home_abbr = short_name.split(" @ ")
            elif " VS " in short_name:
                away_abbr, home_abbr = short_name.split(" VS ")
            else:
                continue
            
            # Get game time for scheduled games
            time_detail = status.get("type", {}).get("detail", "")

            # Filter for your teams if requested
            should_include = True
            if filter_teams:
                if TEST_MODE_RANDOM_2:
                    should_include = True
                    logger.debug(f"Game found: {away_abbr} @ {home_abbr} (TEST MODE - including)")
                else:
                    # Get teams for THIS league only (prevents cross-league matches)
                    league_teams = get_teams_for_league(league)
                    team_match = any(
                        team.upper() in away_abbr.upper() or 
                        team.upper() in home_abbr.upper() 
                        for team in league_teams
                    )
                    should_include = team_match
                    if team_match:
                        logger.debug(f"{league} Game: {away_abbr} @ {home_abbr} - Matched!")
                    else:
                        logger.debug(f"{league} Game: {away_abbr} @ {home_abbr} - Not following")

            if should_include:
                games.append({
                    "home": home_abbr,
                    "away": away_abbr,
                    "home_score": home_score,
                    "away_score": away_score,
                    "clock": clock,
                    "period": period,
                    "state": state,
                    "league": league,
                    "time": time_detail  # Add time for upcoming games
                })
        except Exception as e:
            logger.error(f"Exception processing game {short_name}: {e}")
            continue

    games_count = len(games)
    if filter_teams:
        if TEST_MODE_RANDOM_2:
            logger.info(f"Found {games_count} games total (TEST MODE - all games included)")
        else:
            logger.info(f"Kept {games_count} team games (filtered from {total_games_found} found)")
    else:
        logger.debug(f"Fetched {games_count} games from {league}")
    return games


async def _fetch_all_games_with_cache(use_cache=True):
    """
    Internal function to fetch all games with optional caching.
    
    Args:
        use_cache: If True, return cached data if still valid
    
    Returns:
        List of all game dicts (filtered for your teams)
    """
    global _games_cache
    
    # Check if cache is valid
    if use_cache and _games_cache['data'] is not None and _games_cache['timestamp'] is not None:
        time_since_fetch = (datetime.now() - _games_cache['timestamp']).total_seconds()
        if time_since_fetch < _games_cache['ttl']:
            logger.debug(f"Using cached game data ({int(time_since_fetch)}s old)")
            return _games_cache['data']
    
    # Fetch fresh data
    logger.info(f"Fetching games from {len(API_ENDPOINTS)} endpoints...")
    all_games = []
    for i, url in enumerate(API_ENDPOINTS):
        logger.info(f"[{i+1}/{len(API_ENDPOINTS)}] Fetching from {url.split('/')[-2].upper()}...")
        games = await fetch_games_from_endpoint(url, filter_teams=True)
        all_games.extend(games)
    
    # Update cache
    _games_cache['data'] = all_games
    _games_cache['timestamp'] = datetime.now()
    
    logger.debug(f"Total games fetched: {len(all_games)}")
    return all_games


async def fetch_all_games():
    """
    Fetch all games for your configured teams.
    Uses in-memory cache to avoid redundant API calls.
    
    Returns:
        List of game dicts (all states: live, upcoming, completed)
    """
    return await _fetch_all_games_with_cache(use_cache=False)


async def fetch_upcoming_games(today_only=False):
    """
    Fetch upcoming games scheduled for today (not yet started).
    Reuses cached data from fetch_all_games() to avoid duplicate API calls.
    
    Args:
        today_only: If True, only return games scheduled for today (default: True)
    
    Returns:
        List of game dicts with 'pre' or 'STATUS_SCHEDULED' state
    """
    # Get all games (from cache if available)
    all_games = await _fetch_all_games_with_cache(use_cache=True)
    
    # Filter for only upcoming games (pre-game state)
    upcoming = [
        game for game in all_games 
        if game.get('state') in ['pre', 'STATUS_SCHEDULED']
    ]
    
    # If today_only is True, filter by date
    if today_only:
        from dateutil import parser as date_parser
        today = datetime.now().date()
        filtered_upcoming = []
        
        for game in upcoming:
            time_str = game.get('time', '')
            if not time_str:
                continue
                
            try:
                # dateutil.parser handles ordinal suffixes automatically!
                # "Wed, November 12th at 7:00 PM EST" -> datetime object
                game_datetime = date_parser.parse(time_str)
                game_date = game_datetime.date()
                
                if game_date == today:
                    filtered_upcoming.append(game)
                    
            except Exception as e:
                # If parsing fails, include the game anyway (better to show than hide)
                logger.debug(f"Could not parse game time '{time_str}': {e}")
                filtered_upcoming.append(game)
        
        upcoming = filtered_upcoming
        logger.info(f"Found {len(upcoming)} upcoming games today (from {len(all_games)} total)")
    else:
        logger.info(f"Found {len(upcoming)} upcoming games (from {len(all_games)} total)")
    
    return upcoming


async def fetch_all_live_games():
    """
    Fetch ALL live games across all leagues (not filtered by teams).
    Perfect for ticker mode to show what's happening now.
    
    Returns:
        List of live game dicts across all leagues
    """
    logger.info("Fetching all live games (unfiltered)...")
    all_games = []
    
    for url in API_ENDPOINTS:
        games = await fetch_games_from_endpoint(url, filter_teams=False)
        all_games.extend(games)
    
    # Filter for only live games
    live_games = [
        game for game in all_games
        if game.get('state') in ['inProgress', 'in']
    ]
    
    logger.info(f"Found {len(live_games)} live games across all leagues")
    return live_games


async def fetch_all_upcoming_games():
    """
    Fetch ALL upcoming games today (not filtered by teams).
    Perfect for ticker showing today's full schedule.
    
    Returns:
        List of upcoming game dicts across all leagues
    """
    logger.info("Fetching all upcoming games (unfiltered)...")
    all_games = []
    
    for url in API_ENDPOINTS:
        games = await fetch_games_from_endpoint(url, filter_teams=False)
        all_games.extend(games)
    
    # Filter for only upcoming games
    upcoming = [
        game for game in all_games
        if game.get('state') in ['pre', 'STATUS_SCHEDULED']
    ]
    
    logger.info(f"Found {len(upcoming)} upcoming games across all leagues")
    return upcoming

