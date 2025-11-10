"""
Sports data fetching from ESPN APIs
"""
import httpx
import os
from pathlib import Path

# Load environment variables from config.env if it exists
config_file = Path(__file__).parent / "config.env"
if config_file.exists():
    with open(config_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip())

# --- Settings ---
# Test mode: pick 2 random live games (useful for testing layouts)
TEST_MODE_RANDOM_2 = os.getenv("SPORTS_TEST_MODE", "false").lower() == "true"

# Teams to follow (from environment variables)
TEAMS_NHL = [t.strip() for t in os.getenv("SPORTS_NHL_TEAMS", "DET").split(",") if t.strip()]
TEAMS_NBA = [t.strip() for t in os.getenv("SPORTS_NBA_TEAMS", "DET").split(",") if t.strip()]
TEAMS_NFL = [t.strip() for t in os.getenv("SPORTS_NFL_TEAMS", "DET").split(",") if t.strip()]
TEAMS_MLB = [t.strip() for t in os.getenv("SPORTS_MLB_TEAMS", "DET").split(",") if t.strip()]


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
async def fetch_games_from_endpoint(url):
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
    print(f"📊 Found {total_games_found} total games in {league} scoreboard")

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

            # Filter for your teams (unless in test mode)
            if TEST_MODE_RANDOM_2:
                should_include = True
                print(f"🧪 Game found: {away_abbr} @ {home_abbr} (TEST MODE - including)")
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
                    print(f"✅ {league} Game: {away_abbr} @ {home_abbr} - Matched!")
                else:
                    print(f"⏭️  {league} Game: {away_abbr} @ {home_abbr} - Not following")

            if should_include:
                games.append({
                    "home": home_abbr,
                    "away": away_abbr,
                    "home_score": home_score,
                    "away_score": away_score,
                    "clock": clock,
                    "period": period,
                    "state": state,
                    "league": league
                })
        except Exception as e:
            print(f"❌ Exception processing game {short_name}: {e}")
            continue

    games_count = len(games)
    if TEST_MODE_RANDOM_2:
        print(f"🧪 Found {games_count} games total (TEST MODE - all games included)")
    else:
        print(f"🏙️ Kept {games_count} Detroit games (filtered from {total_games_found} found)")
    return games


async def fetch_all_games():
    print(f"🌐 Starting to fetch games from {len(API_ENDPOINTS)} endpoints...")
    all_games = []
    for i, url in enumerate(API_ENDPOINTS):
        print(f"📡 [{i+1}/{len(API_ENDPOINTS)}] Fetching from {url.split('/')[-2].upper()}...")
        games = await fetch_games_from_endpoint(url)
        all_games.extend(games)
    
    print(f"📈 Total games fetched: {len(all_games)}")
    return all_games

