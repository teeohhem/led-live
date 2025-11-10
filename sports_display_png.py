"""
Sports display rendering using PNG upload (FAST!)
Renders entire scoreboard as PIL Image for instant upload
"""
from PIL import Image, ImageDraw, ImageFont
from sports_data import get_league_letter
import os

# --- Team colors ---
TEAM_COLORS = {
    "DET": (0, 0, 255),
    "MSU": (0, 128, 0),
    "ARK": (255, 0, 0),
    "MICH": (128, 128, 0),
}

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
        print(f"⚠️  Error loading logo for {team_name} ({league}): {e}")
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
        home_color = TEAM_COLORS.get(home_name, (255, 0, 0))
        away_color = TEAM_COLORS.get(away_name, (0, 255, 0))
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
        home_color = TEAM_COLORS.get(home_name, (255,0,0))
        away_color = TEAM_COLORS.get(away_name, (0,255,0))
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
        home_color = TEAM_COLORS.get(home_name, (255,0,0))
        away_color = TEAM_COLORS.get(away_name, (0,255,0))
    
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

