"""
Helper functions for sports rendering.

"""
import os
import logging
from PIL import Image

logger = logging.getLogger(__name__)

# --- Team colors ---
TEAM_COLORS = {
    "NBA": {
        "ATL": (204, 0, 0),      # Atlanta Hawks
        "BOS": (0, 122, 51),     # Boston Celtics
        "BKN": (206, 17, 65),    # Brooklyn Nets
        "CHA": (29, 17, 96),     # Charlotte Hornets
        "CHI": (206, 17, 65),    # Chicago Bulls
        "CLE": (134, 0, 56),     # Cleveland Cavaliers
        "DAL": (0, 83, 188),     # Dallas Mavericks
        "DEN": (13, 34, 64),     # Denver Nuggets
        "DET": (200, 16, 46),    # Detroit Pistons
        "GS": (0, 107, 182),     # Golden State Warriors
        "GSW": (0, 107, 182),    # Golden State Warriors (alternate)
        "HOU": (206, 17, 65),    # Houston Rockets
        "IND": (0, 39, 93),      # Indiana Pacers
        "LAC": (200, 16, 46),    # LA Clippers
        "LAL": (85, 37, 130),    # LA Lakers
        "MEM": (93, 118, 169),   # Memphis Grizzlies
        "MIA": (152, 0, 46),     # Miami Heat
        "MIL": (0, 71, 27),      # Milwaukee Bucks
        "MIN": (0, 80, 131),     # Minnesota Timberwolves
        "NO": (0, 22, 65),       # New Orleans Pelicans
        "NOP": (0, 22, 65),      # New Orleans Pelicans (alternate)
        "NYK": (0, 107, 182),    # New York Knicks
        "OKC": (0, 125, 195),    # Oklahoma City Thunder
        "ORL": (0, 125, 197),    # Orlando Magic
        "PHI": (0, 43, 92),      # Philadelphia 76ers
        "PHX": (229, 96, 32),    # Phoenix Suns
        "POR": (224, 58, 62),    # Portland Trail Blazers
        "SA": (196, 206, 211),   # San Antonio Spurs
        "SAC": (91, 43, 130),    # Sacramento Kings
        "SAS": (196, 206, 211),  # San Antonio Spurs (alternate)
        "TOR": (206, 17, 65),    # Toronto Raptors
        "UT": (0, 43, 92),       # Utah Jazz
        "UTA": (0, 43, 92),      # Utah Jazz (primary)
        "UTH": (0, 43, 92),      # Utah Jazz (alternate)
        "WAS": (0, 34, 68),      # Washington Wizards
        "WSH": (0, 34, 68),      # Washington Wizards (alternate)
    },
    "NHL": {
        "ANA": (247, 73, 2),     # Anaheim Ducks
        "BOS": (252, 181, 20),   # Boston Bruins
        "BUF": (0, 38, 84),      # Buffalo Sabres
        "CGY": (200, 16, 46),    # Calgary Flames
        "CAR": (226, 24, 54),    # Carolina Hurricanes
        "CHI": (207, 10, 44),    # Chicago Blackhawks
        "CBJ": (0, 38, 84),      # Columbus Blue Jackets
        "COL": (111, 38, 61),    # Colorado Avalanche
        "DAL": (0, 104, 71),     # Dallas Stars
        "DET": (200, 16, 46),    # Detroit Red Wings
        "EDM": (4, 30, 66),      # Edmonton Oilers
        "FLA": (200, 16, 46),    # Florida Panthers
        "LA": (85, 37, 130),     # Los Angeles Kings
        "LAK": (85, 37, 130),    # Los Angeles Kings (alternate)
        "MIN": (21, 71, 52),     # Minnesota Wild
        "MTL": (173, 216, 230),  # Montreal Canadiens
        "NSH": (255, 184, 28),   # Nashville Predators
        "NJD": (206, 17, 38),    # New Jersey Devils
        "NYI": (0, 83, 155),     # New York Islanders
        "NYR": (0, 56, 168),     # New York Rangers
        "OTT": (200, 16, 46),    # Ottawa Senators
        "PHI": (247, 73, 2),     # Philadelphia Flyers
        "PIT": (252, 181, 20),   # Pittsburgh Penguins
        "SEA": (111, 38, 51),    # Seattle Kraken
        "SJ": (0, 108, 182),     # San Jose Sharks
        "SJS": (0, 108, 182),    # San Jose Sharks (alternate)
        "STL": (0, 47, 135),     # St. Louis Blues
        "TBL": (0, 32, 91),      # Tampa Bay Lightning
        "TOR": (0, 32, 91),      # Toronto Maple Leafs
        "UTA": (111, 38, 61),    # Utah Hockey Club
        "VAN": (0, 32, 91),      # Vancouver Canucks
        "VGK": (185, 151, 91),   # Vegas Golden Knights
        "WPG": (4, 30, 66),      # Winnipeg Jets
        "WSH": (4, 30, 66),      # Washington Capitals
    },
    "NFL": {
        "ARI": (151, 35, 63),    # Arizona Cardinals
        "ATL": (167, 25, 48),    # Atlanta Falcons
        "BAL": (26, 25, 95),     # Baltimore Ravens
        "BUF": (0, 51, 160),     # Buffalo Bills
        "CAR": (0, 133, 202),    # Carolina Panthers
        "CHI": (230, 65, 0),     # Chicago Bears
        "CIN": (255, 60, 0),     # Cincinnati Bengals
        "CLE": (49, 29, 0),      # Cleveland Browns
        "DAL": (0, 53, 148),     # Dallas Cowboys
        "DEN": (255, 90, 31),    # Denver Broncos
        "DET": (0, 118, 182),    # Detroit Lions
        "GB": (24, 48, 40),      # Green Bay Packers
        "HOU": (3, 32, 47),      # Houston Texans
        "IND": (0, 44, 95),      # Indianapolis Colts
        "JAX": (0, 103, 120),    # Jacksonville Jaguars
        "KC": (235, 0, 41),      # Kansas City Chiefs
        "LV": (0, 0, 0),         # Las Vegas Raiders
        "LAC": (0, 128, 198),    # LA Chargers
        "LAR": (0, 53, 148),     # LA Rams
        "MIA": (0, 142, 151),    # Miami Dolphins
        "MIN": (79, 38, 131),    # Minnesota Vikings
        "NE": (0, 34, 68),       # New England Patriots
        "NO": (162, 170, 173),   # New Orleans Saints
        "NYG": (1, 35, 82),      # New York Giants
        "NYJ": (18, 87, 64),     # New York Jets
        "PHI": (0, 76, 84),      # Philadelphia Eagles
        "PIT": (255, 182, 18),   # Pittsburgh Steelers
        "SEA": (0, 34, 68),      # Seattle Seahawks
        "SF": (170, 0, 0),       # San Francisco 49ers
        "TB": (213, 10, 10),     # Tampa Bay Buccaneers
        "TEN": (12, 35, 64),     # Tennessee Titans
        "WSH": (90, 20, 0),      # Washington Commanders
    },
    "MLB": {
        # Baseball teams...
    },
}

# Team abbreviation mapping (ESPN API → Logo filename)
TEAM_ABBR_MAP = {
    "NBA": {
        "GSW": "GS",
        "SAS": "SA",
        "NOP": "NO",
        "WAS": "WSH",
        "UTH": "UTA",
        "UT": "UTA",
    },
    "NHL": {
        "LAK": "LA",
        "SJS": "SJ",
    },
    "NFL": {},
    "MLB": {},
}


def get_team_color(team_name, league, default=(255, 255, 255)):
    """
    Get the primary color for a team.
    
    Args:
        team_name: Team abbreviation
        league: League name (NBA, NHL, NFL, MLB)
        default: Default color if team not found
    
    Returns:
        (R, G, B) tuple
    """
    league_colors = TEAM_COLORS.get(league, {})
    return league_colors.get(team_name, default)


def normalize_team_abbr(team_name, league):
    """
    Normalize team abbreviation from ESPN API to match logo filename.
    
    Args:
        team_name: Team abbreviation from ESPN API
        league: League name (NBA, NHL, NFL, MLB)
    
    Returns:
        Normalized team abbreviation matching logo filename
    """
    league_map = TEAM_ABBR_MAP.get(league, {})
    return league_map.get(team_name, team_name)


def load_team_logo(team_name, league, max_size=(16, 16)):
    """
    Load team logo from league-specific folder.
    Structure: logos/{league}/{team_name}.png
    
    Falls back to logos/NOT_FOUND.png if team logo doesn't exist.
    Returns PIL Image or None if neither logo nor fallback exists.
    """
    # Normalize team abbreviation to match logo filename
    team_name = normalize_team_abbr(team_name, league)
    
    # Normalize league name to lowercase for folder
    league_folder = league.lower() if league else "unknown"
    logo_path = f"./logos/{league_folder}/{team_name}.png"
    
    # Try team-specific logo first
    if not os.path.exists(logo_path):
        # Fall back to NOT_FOUND.png
        logo_path = "./logos/NOT_FOUND.png"
        if not os.path.exists(logo_path):
            return None
    
    try:
        logo = Image.open(logo_path).convert("RGBA")
        
        # Auto-crop transparent borders
        bbox = logo.getbbox()
        if bbox:
            logo = logo.crop(bbox)
        
        # Preserve aspect ratio when resizing
        logo.thumbnail(max_size, Image.LANCZOS)
        
        return logo
    except Exception as e:
        logger.warning(f"Error loading logo for {team_name} ({league}): {e}")
        return None

