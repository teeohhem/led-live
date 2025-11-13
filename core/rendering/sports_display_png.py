"""
Sports display rendering using PNG upload (FAST!)
Renders entire scoreboard as PIL Image for instant upload
"""
from PIL import Image, ImageDraw, ImageFont
from core.data.sports_data import get_league_letter
from datetime import datetime
import os
import logging
logger = logging.getLogger(__name__)


def format_game_time(time_str, compact=False):
    """
    Format game time intelligently based on date.
    
    Args:
        time_str: Time string from ESPN (e.g., "Wed, November 12th at 7:00 PM EST")
        compact: If True, use more abbreviated format
    
    Returns:
        Formatted string:
        - Today: "7:00 PM" or "7PM" (compact)
        - This week: "Wed 7PM"
        - Further: "Nov 15"
    """
    if not time_str:
        return "TBD"
    
    try:
        from dateutil import parser as date_parser
        
        game_datetime = date_parser.parse(time_str)
        today = datetime.now().date()
        game_date = game_datetime.date()
        
        if game_date == today:
            # Today - just show time
            if compact:
                return game_datetime.strftime('%I%p').lstrip('0')  # "7PM"
            else:
                return game_datetime.strftime('%I:%M %p').lstrip('0')  # "7:00 PM"
        else:
            # Future game - show date info
            days_away = (game_date - today).days
            if days_away <= 6:
                # This week: "Wed 7PM"
                hour = game_datetime.strftime('%I').lstrip('0')  # Remove leading zero
                period = game_datetime.strftime('%p')
                day = game_datetime.strftime('%a')
                return f"{day} {hour}{period}"
            else:
                # Further out: "Nov 15"
                return game_datetime.strftime('%b %d')
    except Exception as e:
        # Fallback: try to extract time from string
        if 'at' in time_str:
            time_part = time_str.split('at')[1].strip()
            parts = time_part.split()
            if compact and len(parts) >= 2:
                return parts[0] + parts[1]  # "7:00PM"
            elif len(parts) >= 2:
                return parts[0] + ' ' + parts[1]  # "7:00 PM"
        return time_str


# --- Team colors ---
TEAM_COLORS = {
    "NBA": {
        "ATL": (204, 0, 0),      # Atlanta Hawks
        "BOS": (0, 122, 51),     # Boston Celtics
        "BKN": (0, 0, 0),        # Brooklyn Nets
        "CHA": (29, 17, 96),     # Charlotte Hornets
        "CHI": (206, 17, 65),    # Chicago Bulls
        "CLE": (134, 0, 56),     # Cleveland Cavaliers
        "DAL": (0, 83, 188),     # Dallas Mavericks
        "DEN": (13, 34, 64),     # Denver Nuggets
        "DET": (200, 16, 46),    # Detroit Pistons
        "GSW": (0, 107, 182),    # Golden State Warriors
        "HOU": (206, 17, 65),    # Houston Rockets
        "IND": (0, 39, 93),      # Indiana Pacers
        "LAC": (200, 16, 46),    # LA Clippers
        "LAL": (85, 37, 130),    # LA Lakers
        "MEM": (93, 118, 169),   # Memphis Grizzlies
        "MIA": (152, 0, 46),     # Miami Heat
        "MIL": (0, 71, 27),      # Milwaukee Bucks
        "MIN": (0, 80, 131),     # Minnesota Timberwolves
        "NOP": (0, 22, 65),      # New Orleans Pelicans
        "NYK": (0, 107, 182),    # New York Knicks
        "OKC": (0, 125, 195),    # Oklahoma City Thunder
        "ORL": (0, 125, 197),    # Orlando Magic
        "PHI": (0, 43, 92),      # Philadelphia 76ers
        "PHX": (229, 96, 32),    # Phoenix Suns
        "POR": (224, 58, 62),    # Portland Trail Blazers
        "SAC": (91, 43, 130),    # Sacramento Kings
        "SAS": (196, 206, 211),  # San Antonio Spurs
        "TOR": (206, 17, 65),    # Toronto Raptors
        "UTA": (0, 43, 92),      # Utah Jazz
        "WAS": (0, 34, 68),      # Washington Wizards
    },
    "NFL": {
        "ARI": (151, 35, 63),    # Arizona Cardinals
        "ATL": (167, 25, 48),    # Atlanta Falcons
        "BAL": (26, 25, 95),     # Baltimore Ravens
        "BUF": (0, 51, 160),     # Buffalo Bills
        "CAR": (0, 133, 202),    # Carolina Panthers
        "CHI": (11, 22, 42),     # Chicago Bears
        "CIN": (255, 60, 0),     # Cincinnati Bengals
        "CLE": (49, 29, 0),      # Cleveland Browns
        "DAL": (0, 53, 148),     # Dallas Cowboys
        "DEN": (255, 90, 31),    # Denver Broncos
        "DET": (0, 118, 182),    # Detroit Lions
        "GB": (24, 48, 40),      # Green Bay Packers
        "HOU": (3, 32, 47),      # Houston Texans
        "IND": (0, 44, 95),      # Indianapolis Colts
        "JAX": (0, 103, 120),    # Jacksonville Jaguars
        "KC": (141, 144, 149),   # Kansas City Chiefs
        "LAC": (0, 128, 198),    # LA Chargers
        "LAR": (79, 38, 131),    # LA Rams
        "LVR": (0, 0, 0),        # Las Vegas Raiders
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
    "NHL": {
        "ANA": (247, 73, 2),     # Anaheim Ducks
        "ARI": (140, 38, 51),    # Arizona Coyotes
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
        "LAK": (0, 0, 0),        # Los Angeles Kings
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
        "SJS": (0, 108, 182),    # San Jose Sharks
        "STL": (0, 47, 135),     # St. Louis Blues
        "TBL": (0, 32, 91),      # Tampa Bay Lightning
        "TOR": (0, 32, 91),      # Toronto Maple Leafs
        "VAN": (0, 32, 91),      # Vancouver Canucks
        "VGK": (185, 151, 91),   # Vegas Golden Knights
        "WPG": (4, 30, 66),      # Winnipeg Jets
        "WSH": (4, 30, 66),      # Washington Capitals
    },
    "MLB": {
        "ARI": (167, 25, 48),    # Arizona Diamondbacks
        "ATL": (206, 17, 38),    # Atlanta Braves
        "BAL": (223, 70, 1),     # Baltimore Orioles
        "BOS": (189, 48, 57),    # Boston Red Sox
        "CHC": (14, 51, 134),    # Chicago Cubs
        "CIN": (198, 1, 31),     # Cincinnati Reds
        "CLE": (134, 38, 51),    # Cleveland Guardians
        "COL": (51, 0, 114),     # Colorado Rockies
        "CWS": (0, 0, 0),        # Chicago White Sox
        "DET": (12, 35, 64),     # Detroit Tigers
        "HOU": (0, 45, 98),      # Houston Astros
        "KC": (0, 70, 135),      # Kansas City Royals
        "LAA": (186, 0, 33),     # LA Angels
        "LAD": (0, 90, 156),     # LA Dodgers
        "MIA": (0, 163, 224),    # Miami Marlins
        "MIL": (19, 41, 75),     # Milwaukee Brewers
        "MIN": (0, 43, 92),      # Minnesota Twins
        "NYM": (0, 45, 114),     # New York Mets
        "NYY": (0, 48, 135),     # New York Yankees
        "OAK": (0, 56, 49),      # Oakland Athletics
        "PHI": (232, 24, 40),    # Philadelphia Phillies
        "PIT": (253, 184, 39),   # Pittsburgh Pirates
        "SD": (0, 45, 98),       # San Diego Padres
        "SEA": (0, 92, 92),      # Seattle Mariners
        "SF": (253, 90, 30),     # San Francisco Giants
        "STL": (196, 30, 58),    # St. Louis Cardinals
        "TB": (9, 44, 92),       # Tampa Bay Rays
        "TEX": (0, 50, 120),     # Texas Rangers
        "TOR": (19, 74, 142),    # Toronto Blue Jays
        "WSH": (171, 0, 3),      # Washington Nationals
    },
    "COLLEGE": {
        "MSU": (0, 128, 0),      # Michigan State
        "ARK": (255, 0, 0),      # Arkansas
        "MICH": (128, 128, 0),   # Michigan
    }
}

def get_team_color(team_name, league, default_color=(255, 0, 0)):
    """
    Get team color by league and team name.
    Falls back to default_color if team/league not found.
    """
    league_colors = TEAM_COLORS.get(league, {})
    return league_colors.get(team_name, default_color)

# --- Logo Loading ---
def load_team_logo(team_name, league, max_size=(16, 16)):
    """
    Load team logo from league-specific folder.
    Structure: logos/{league}/{team_name}.png
    
    Examples:
        - logos/nhl/DET.png
        - logos/nba/DET.png
        - logos/nfl/DET.png
    
    Falls back to logos/NOT_FOUND.png if team logo doesn't exist.
    Automatically crops transparent borders and preserves aspect ratio!
    Returns PIL Image or None if neither logo nor fallback exists.
    """
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
        
        # Auto-crop transparent borders to get actual logo bounds
        # Get bounding box of non-transparent pixels
        bbox = logo.getbbox()
        if bbox:
            logo = logo.crop(bbox)
        
        # Preserve aspect ratio when resizing
        logo.thumbnail(max_size, Image.LANCZOS)
        
        return logo
    except Exception as e:
        logger.warning(f"Errorloadinglogofor{team_name}({league}):{e}")
        return None


def render_game_with_logos(img, game, width=64, height=40):
    """
    Render a single game in FULL-SCREEN format with LOGOS (40 rows).
    Beautiful layout for single game display.
    
    Layout:
      Top half (20px): Away team logo + score
      Bottom half (20px): Home team logo + score
      Right side: Period + Clock
    """
    draw = ImageDraw.Draw(img)
    
    # Fonts
    try:
        score_font = ImageFont.truetype("./fonts/PixelOperator.ttf", 14)
        team_font = ImageFont.truetype("./fonts/PixelOperator.ttf", 10)
        small_font = ImageFont.truetype("./fonts/PixelOperator.ttf", 8)
    except OSError:
        score_font = ImageFont.load_default()
        team_font = score_font
        small_font = score_font
    
    home_name = game["home"]
    away_name = game["away"]
    home_score = str(game["home_score"])
    away_score = str(game["away_score"])
    clock = game.get("clock", "")
    period = game.get("period", "")
    league = game.get("league", "")
    
    # Check if game is over
    game_state = game.get("state", "")
    is_game_over = game_state in ["post", "completed", "final"]
    
    if is_game_over:
        home_color = (150, 150, 150)
        away_color = (150, 150, 150)
        time_color = (150, 150, 150)
    else:
        home_color = get_team_color(home_name, league, (255, 0, 0))
        away_color = get_team_color(away_name, league, (0, 255, 0))
        time_color = (255, 255, 0)
    
    # --- AWAY TEAM (top half, y=0-19) ---
    away_logo = load_team_logo(away_name, league, max_size=(16, 16))
    if away_logo:
        # Logo exists (or fallback NOT_FOUND.png) - composite it
        img.paste(away_logo, (2, 2), away_logo)  # Alpha blend at (2, 2)
    
    # Away score (large, to the right of logo)
    draw.text((22, 2), away_score, fill=away_color, font=score_font)
    
    # --- HOME TEAM (bottom half, y=20-39) ---
    home_logo = load_team_logo(home_name, league, max_size=(16, 16))
    if home_logo:
        # Logo exists (or fallback NOT_FOUND.png) - composite it
        img.paste(home_logo, (2, 22), home_logo)  # Alpha blend at (2, 22)
    
    # Home score (large, to the right of logo)
    draw.text((22, 22), home_score, fill=home_color, font=score_font)
    
    # --- PERIOD + CLOCK (right side, top panel) ---
    if is_game_over:
        period_text = "END"
    else:
        period_text = period if period else ""
    
    if period_text:
        # Position period on TOP panel (y=0-19)
        period_bbox = small_font.getbbox(period_text)
        period_width = period_bbox[2] - period_bbox[0]
        period_x = width - period_width - 3
        period_y = 2  # Top of display, stays in top panel
        draw.text((period_x, period_y), period_text, fill=time_color, font=small_font)
        
        # Clock below period (still on top panel)
        if clock and not is_game_over:
            clock_y = period_y + 9  # Below period, still within top panel (y < 20)
            clock_bbox = small_font.getbbox(clock)
            clock_width = clock_bbox[2] - clock_bbox[0]
            clock_x = width - clock_width - 3
            draw.text((clock_x, clock_y), clock, fill=time_color, font=small_font)


def render_game_expanded(draw, game, offset=(0,0), width=64, font=None, small_font=None):
    """
    Render a single game in EXPANDED format (20 rows).
    Draws directly onto a PIL ImageDraw object.
    Layout:
      Left: Team names + scores (away top, home bottom)
      Right: Period (top right) with clock below
    """
    if font is None:
        try:
            font = ImageFont.truetype("./fonts/PixelOperator.ttf", 10)
        except OSError:
            font = ImageFont.load_default()
    
    if small_font is None:
        small_font = font
    
    home_name = game["home"]
    away_name = game["away"]
    home_score = str(game["home_score"])
    away_score = str(game["away_score"])
    clock = game.get("clock", "")
    period = game.get("period", "")
    
    # Shorten team names
    home_abbr = home_name[:3]
    away_abbr = away_name[:3]
    
    # Check if game is over
    game_state = game.get("state", "")
    is_game_over = game_state in ["post", "completed", "final"]
    
    if is_game_over:
        home_color = (150, 150, 150)
        away_color = (150, 150, 150)
        time_color = (150, 150, 150)
    else:
        home_color = get_team_color(home_name, league, (255,0,0))
        away_color = get_team_color(away_name, league, (0,255,0))
        time_color = (255, 255, 0)

    x_start, y_start = offset
    
    # Get font size for dynamic spacing
    font_size = font.size if hasattr(font, 'size') else 10
    # Use tighter spacing to ensure both lines fit in 20 pixels
    vertical_spacing = 11  # Fixed spacing to ensure home team at y_start+11 fits with small font
    
    # --- AWAY TEAM (top left) ---
    away_text = f"{away_abbr} {away_score}"
    draw.text((x_start + 2, y_start + 1), away_text, fill=away_color, font=font)
    
    # --- HOME TEAM (middle left) ---
    home_y = y_start + vertical_spacing
    home_text = f"{home_abbr} {home_score}"
    draw.text((x_start + 2, home_y), home_text, fill=home_color, font=font)
    
    # --- PERIOD (top right) ---
    if is_game_over:
        period_text = "END"
    else:
        period_text = period if period else ""
    
    if period_text:
        period_bbox = small_font.getbbox(period_text)
        period_width = period_bbox[2] - period_bbox[0]
        period_x = width - period_width - 4
        period_y = y_start + 1
        draw.text((period_x, period_y), period_text, fill=time_color, font=small_font)
    
    # --- CLOCK (right side, below period) ---
    if clock and not is_game_over:
        clock_bbox = small_font.getbbox(clock)
        clock_width = clock_bbox[2] - clock_bbox[0]
        clock_x = width - clock_width - 4
        clock_y = home_y
        draw.text((clock_x, clock_y), clock, fill=time_color, font=small_font)


def render_game_compact(draw, game, offset=(0,0), width=64, font=None):
    """
    Render a single game in COMPACT format (10 rows) - single line only.
    Layout: Away team + score (left) | Home team + score (right)
    """
    if font is None:
        try:
            font = ImageFont.truetype("./fonts/PixelOperator.ttf", 10)
        except OSError:
            font = ImageFont.load_default()
    
    home_name = game["home"]
    away_name = game["away"]
    home_score = str(game["home_score"])
    away_score = str(game["away_score"])
    
    # Shorten team names
    home_abbr = home_name[:3]
    away_abbr = away_name[:3]
    
    # Check if game is over
    game_state = game.get("state", "")
    is_game_over = game_state in ["post", "completed", "final"]
    
    if is_game_over:
        home_color = (150, 150, 150)
        away_color = (150, 150, 150)
    else:
        home_color = get_team_color(home_name, league, (255,0,0))
        away_color = get_team_color(away_name, league, (0,255,0))

    x_start, y_start = offset
    y_center = y_start + 1
    
    # --- LEFT: AWAY TEAM + SCORE ---
    away_text = f"{away_abbr} {away_score}"
    draw.text((x_start + 1, y_center), away_text, fill=away_color, font=font)
    
    # --- RIGHT: HOME TEAM + SCORE ---
    home_text = f"{home_abbr} {home_score}"
    home_bbox = font.getbbox(home_text)
    home_width = home_bbox[2] - home_bbox[0]
    home_x = width - home_width - 2
    draw.text((home_x, y_center), home_text, fill=home_color, font=font)


def render_scoreboard_single_game_fullscreen(img, game, width=64, height=40):
    """
    Layout Format: SINGLE GAME - FULL SCREEN WITH LOGOS
    - Full 40 pixel height
    - Team logos (16x16) on left side
    - Large scores next to logos
    - Period and clock in top-right corner
    """
    render_game_with_logos(img, game, width=width, height=height)


def render_scoreboard_two_games_expanded(img, games, width=64, height=40):
    """
    Layout Format: TWO GAMES - EXPANDED (20 pixels per game)
    - Game 1: Top panel (y=0-19)
    - Game 2: Bottom panel (y=20-39)
    - Shows: team names, scores, period, clock
    - Font: 10px main, 8px details
    """
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("./fonts/PixelOperator.ttf", 10)
        small_font = ImageFont.truetype("./fonts/PixelOperator.ttf", 8)
    except OSError:
        font = ImageFont.load_default()
        small_font = font
    
    for i, game in enumerate(games):
        y_offset = i * 20  # Each game gets exactly 20 pixels
        render_game_expanded(draw, game, offset=(0, y_offset), width=width, font=font, small_font=small_font)


def render_scoreboard_multi_game_compact(img, games, width=64, height=40):
    """
    Layout Format: 3-4 GAMES - COMPACT (single line per game)
    - Shows: abbreviated team names + scores only
    - Font: 10px
    - Positions AVOID panel boundary at y=20 to prevent text bleeding!
    
    Panel Layout:
      Top Panel (y=0-19):    Games 0-1
      Bottom Panel (y=20-39): Games 2-3
    """
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("./fonts/PixelOperator.ttf", 10)
    except OSError:
        font = ImageFont.load_default()
    
    num_games = len(games)
    
    # CRITICAL: Position games to avoid y=20 boundary!
    # Each compact game is ~10 pixels tall
    if num_games == 3:
        # 3 games: 2 on top panel, 1 on bottom panel
        # Top panel positioning (maximize space usage):
        #   - Game 0: y=1 (extends to ~y=11)
        #   - Game 1: y=9 (extends to ~y=19, safely within top panel)
        # Bottom panel:
        #   - Game 2: y=22 (extends to ~y=32)
        positions = [1, 9, 22]
    else:  # 4 games
        # 4 games: 2 on each panel
        # Top panel: Games 0-1
        # Bottom panel: Games 2-3
        positions = [1, 9, 21, 30]
    
    for i, game in enumerate(games):
        y_offset = positions[i]
        render_game_compact(draw, game, offset=(0, y_offset), width=width, font=font)


def render_scoreboard(games, width=64, height=40):
    """
    Render complete scoreboard as PIL Image (FAST PNG upload!).
    
    Adaptive layout based on number of games:
    - 1 game:   Full-screen with logos (render_scoreboard_single_game_fullscreen)
    - 2 games:  Expanded format, 20px per game (render_scoreboard_two_games_expanded)
    - 3-4 games: Compact format, single line per game (render_scoreboard_multi_game_compact)
    
    Returns:
        PIL Image (RGB mode, 64x40)
    """
    # Create black background
    img = Image.new('RGB', (width, height), color=(0, 0, 0))
    
    num_games = len(games)
    if num_games == 0:
        return img
    
    # Limit to 4 games max
    games = games[:4]
    num_games = len(games)
    
    if num_games == 1:
        render_scoreboard_single_game_fullscreen(img, games[0], width=width, height=height)
    elif num_games == 2:
        render_scoreboard_two_games_expanded(img, games, width=width, height=height)
    else:  # 3 or 4 games
        render_scoreboard_multi_game_compact(img, games, width=width, height=height)
    
    return img


def render_upcoming_games(games, width=64, height=40):
    """
    Render upcoming games scheduled for today with team logos.
    
    Shows:
    - Team logos (away @ home)
    - Game time
    - League indicator
    
    Layout:
    - 1 game: Large format with logos (similar to live game display)
    - 2 games: Stacked format with small logos, 20px per game
    - 3-4 games: Compact format with mini logos, 10px per game
    
    Args:
        games: List of upcoming game dicts from fetch_upcoming_games()
        width: Image width (default 64)
        height: Image height (default 40)
    
    Returns:
        PIL Image (RGB mode)
    """
    img = Image.new('RGB', (width, height), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    num_games = len(games)
    if num_games == 0:
        # No upcoming games
        try:
            font = ImageFont.truetype("./fonts/PixelOperator.ttf", 8)
        except:
            font = ImageFont.load_default()
        draw.text((4, 8), "No games today", fill=(128, 128, 128), font=font)
        return img
    
    # Limit to 4 games max
    games = games[:4]
    num_games = len(games)
    
    try:
        font_large = ImageFont.truetype("./fonts/PixelOperator.ttf", 12)
        font_medium = ImageFont.truetype("./fonts/PixelOperator.ttf", 10)
        font_small = ImageFont.truetype("./fonts/PixelOperator.ttf", 8)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    if num_games == 1:
        # Single game - large format with logos (similar to live games)
        game = games[0]
        away = game['away']
        home = game['home']
        time = game['time']
        league = game['league']
        
        # Away team logo (top half)
        away_logo = load_team_logo(away, league, max_size=(16, 16))
        if away_logo:
            img.paste(away_logo, (2, 2), away_logo)
        
        # Away team name
        draw.text((22, 4), away, fill=(200, 200, 200), font=font_medium)
        
        # @ symbol in middle
        draw.text((width // 2 - 3, 12), "@", fill=(100, 100, 100), font=font_small)
        
        # Home team logo (bottom half)
        home_logo = load_team_logo(home, league, max_size=(16, 16))
        if home_logo:
            img.paste(home_logo, (2, 22), home_logo)
        
        # Home team name
        draw.text((22, 24), home, fill=(255, 255, 255), font=font_medium)
        
        # Format time (shows date if not today)
        time_display = format_game_time(time, compact=False)
        
        # Right-align and center vertically
        time_bbox = font_small.getbbox(time_display)
        time_width = time_bbox[2] - time_bbox[0]
        time_x = width - time_width - 2
        draw.text((time_x, 10), time_display, fill=(100, 200, 255), font=font_small)
        
    elif num_games == 2:
        # Two games - stacked format with logos side-by-side (20px each)
        for idx, game in enumerate(games):
            y_offset = idx * 20
            away = game['away']
            home = game['home']
            time = game['time']
            league = game['league']
            
            # Away logo (small, 10x10) on left
            away_logo = load_team_logo(away, league, max_size=(10, 10))
            if away_logo:
                img.paste(away_logo, (2, y_offset + 5), away_logo)
            
            # Away team name next to logo
            draw.text((14, y_offset + 6), away, fill=(200, 200, 200), font=font_small)
            
            # @ symbol
            draw.text((29, y_offset + 6), "@", fill=(100, 100, 100), font=font_medium)
            
            # Home logo (small, 10x10) 
            home_logo = load_team_logo(home, league, max_size=(10, 10))
            if home_logo:
                img.paste(home_logo, (34, y_offset + 5), home_logo)
            
            # Home team name next to logo
            draw.text((46, y_offset + 6), home, fill=(255, 255, 255), font=font_small)
            
            # Format time (shows date if not today)
            time_display = format_game_time(time, compact=False)
            
            # Right-align time on second line of this game
            time_bbox = font_small.getbbox(time_display)
            time_width = time_bbox[2] - time_bbox[0]
            time_x = width - time_width - 2
            draw.text((time_x, y_offset + 12), time_display, fill=(100, 200, 255), font=font_small)
    
    else:
        # 3-4 games - compact format with mini logos (10px each)
        for idx, game in enumerate(games):
            y_offset = idx * 10
            away = game['away']
            home = game['home']
            time = game['time']
            league = game['league']
            
            # Away logo (mini, 8x8)
            away_logo = load_team_logo(away, league, max_size=(8, 8))
            if away_logo:
                img.paste(away_logo, (2, y_offset + 1), away_logo)
            
            # Away team name (abbreviated)
            draw.text((12, y_offset + 1), away[:3], fill=(200, 200, 200), font=font_small)
            
            # @ symbol
            draw.text((26, y_offset + 1), "@", fill=(100, 100, 100), font=font_small)
            
            # Home team name (abbreviated)
            draw.text((30, y_offset + 1), home[:3], fill=(255, 255, 255), font=font_small)
            
            # Format time (compact for 3-4 games)
            time_display = format_game_time(time, compact=True)
            
            # Right-align time
            time_bbox = font_small.getbbox(time_display)
            time_width = time_bbox[2] - time_bbox[0]
            time_x = width - time_width - 2
            draw.text((time_x, y_offset + 1), time_display, fill=(100, 200, 255), font=font_small)
    
    return img

