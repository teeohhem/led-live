"""
All-in-one display manager for dual LED panels (PNG UPLOAD VERSION - FAST!)
Intelligently switches between:
1. Sports (priority when Detroit games are live) - with team logos!
2. Themed Clock + Weather (cycles when no sports) - customizable themes!
3. Full Weather Display (cycles with clock when no sports)

Features:
- PNG upload for instant display updates
- Custom clock themes (Stranger Things, Matrix, Classic, etc.)
- Team logos with automatic fallback
- Auto-cropping and aspect ratio preservation
- Live game priority filtering
- Weather forecasts: Hourly OR Daily (configurable!)

See CLOCK_THEMES.md for theme customization!

Weather Forecast Settings:
- WEATHER_FORECAST_MODE = "daily"   → Shows next 2 days (Mon, Tue)
- WEATHER_FORECAST_MODE = "hourly"  → Shows next hours (2PM, 5PM)
"""
import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from adapters.base import DisplayAdapter

# Load environment variables from config.env if it exists
config_file = "./config.env"
if os.path.exists(config_file):
    with open(config_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip())

# Import shared modules
from panel_core import set_display_adapter, get_display_adapter
from adapters import get_adapter

# --- Settings (from environment variables) ---
SPORTS_CHECK_INTERVAL = int(os.getenv("SPORTS_CHECK_INTERVAL", "10"))
WEATHER_CHECK_INTERVAL = int(os.getenv("WEATHER_CHECK_INTERVAL", "1800"))
MODE_CHECK_INTERVAL = int(os.getenv("DISPLAY_MODE_CHECK_INTERVAL", "2"))

# Display settings (from environment variables)
CLOCK_THEME = os.getenv("CLOCK_THEME", "stranger_things")  # Clock theme
CLOCK_24H = os.getenv("CLOCK_24H", "false").lower() == "true"  # 24-hour format
WEATHER_FORECAST_MODE = os.getenv("WEATHER_FORECAST_MODE", "daily")  # Forecast type

# Display mode configuration
DISPLAY_SPORTS_PRIORITY = os.getenv("DISPLAY_SPORTS_PRIORITY", "true").lower() == "true"
DISPLAY_CYCLE_MODES = [m.strip() for m in os.getenv("DISPLAY_CYCLE_MODES", "clock,weather").split(",") if m.strip()]
DISPLAY_CYCLE_SECONDS = int(os.getenv("DISPLAY_CYCLE_SECONDS", "300"))  # 5 minutes default

# PNG refresh intervals (keeps displays visible)
DISPLAY_SPORTS_REFRESH_INTERVAL = int(os.getenv("DISPLAY_SPORTS_REFRESH_INTERVAL", "2"))
DISPLAY_WEATHER_REFRESH_INTERVAL = int(os.getenv("DISPLAY_WEATHER_REFRESH_INTERVAL", "2"))
DISPLAY_CLOCK_REFRESH_INTERVAL = int(os.getenv("DISPLAY_CLOCK_REFRESH_INTERVAL", "2"))
DISPLAY_STOCKS_REFRESH_INTERVAL = int(os.getenv("DISPLAY_STOCKS_REFRESH_INTERVAL", "2"))

# Visual preferences
SPORTS_SHOW_LOGOS = os.getenv("SPORTS_SHOW_LOGOS", "true").lower() == "true"
WEATHER_SHOW_ICONS = os.getenv("WEATHER_SHOW_ICONS", "true").lower() == "true"


# --- Clock rendering now uses custom PNG themes! See clock_display_png.py ---


# --- Mode Manager ---
class DisplayMode:
    SPORTS = "sports"
    CLOCK = "clock"
    WEATHER = "weather"
    STOCKS = "stocks"


async def get_live_detroit_games(games):
    """Filter for only live Detroit games"""
    live_detroit = []
    for game in games:
        state = game.get("state", "")
        # Check if live (in progress)
        is_live = state == "inProgress" or state == "in"
        
        if is_live:
            live_detroit.append(game)
    
    return live_detroit


def should_show_sports(games):
    """Determine if we should show sports mode (any live Detroit games)"""
    for game in games:
        state = game.get("state", "")
        if state == "inProgress" or state == "in":
            return True
    return False


def filter_live_games(games):
    """
    Filter games to prioritize live games.
    If any live games exist, return only live games.
    Otherwise, return all games.
    """
    live_games = [g for g in games if g.get("state", "") in ["inProgress", "in"]]
    if live_games:
        print(f"  🔴 {len(live_games)} live game(s) found - showing only live games")
        return live_games
    return games


# --- Main Application ---
async def main(display_adapter: Optional[DisplayAdapter] = None):
    """
    Main display manager function.

    Args:
        display_adapter: DisplayAdapter instance to use. If None, uses BLE adapter for backward compatibility.
    """
    # Validate configuration
    valid_modes = {DisplayMode.SPORTS, DisplayMode.CLOCK, DisplayMode.WEATHER, DisplayMode.STOCKS}
    invalid_modes = [m for m in DISPLAY_CYCLE_MODES if m not in valid_modes]
    if invalid_modes:
        print(f"❌ Invalid display modes in config: {invalid_modes}")
        print(f"   Valid modes: sports, clock, weather, stocks")
        return

    if not DISPLAY_CYCLE_MODES:
        print(f"❌ No display modes configured! Set DISPLAY_CYCLE_MODES in config.env")
        return

    # Use provided adapter or default to iPixel 20x64 adapter
    if display_adapter is None:
        from adapters import get_adapter
        display_adapter = get_adapter('ipixel20x64')

    # Set the adapter in panel_core for backward compatibility
    set_display_adapter(display_adapter)

    # Import data modules early (needed for configuration display)
    from core.data import CITY, STOCKS_SYMBOLS, STOCKS_CHECK_INTERVAL

    # Get adapter info for display
    try:
        adapter_info = await display_adapter.get_info()
        adapter_type = adapter_info.get('adapter_type', 'unknown')
        panel_count = adapter_info.get('device_count', 1)
        width = display_adapter.display_width
        height = display_adapter.display_height
    except:
        adapter_type = 'unknown'
        panel_count = 1
        width = 64
        height = 40

    print("🚀 Starting ALL-IN-ONE Display Manager...")
    print(f"📺 Display: {height}x{width} ({panel_count} panels) via {adapter_type}")
    print(f"🔄 Cycle Modes: {' → '.join(DISPLAY_CYCLE_MODES)}")
    print(f"⏱️  Cycle Duration: {DISPLAY_CYCLE_SECONDS}s per mode")

    # Show config for each mode in cycle
    if DisplayMode.SPORTS in DISPLAY_CYCLE_MODES:
        print(f"🏀 Sports Priority: {'ON' if DISPLAY_SPORTS_PRIORITY else 'OFF'}")
    if DisplayMode.STOCKS in DISPLAY_CYCLE_MODES:
        print(f"📈 Stocks: {', '.join(STOCKS_SYMBOLS)}")
    if DisplayMode.WEATHER in DISPLAY_CYCLE_MODES or DisplayMode.CLOCK in DISPLAY_CYCLE_MODES:
        print(f"🌍 Weather: {CITY}")
    if DisplayMode.CLOCK in DISPLAY_CYCLE_MODES:
        print(f"🕐 Clock Theme: {CLOCK_THEME}")

    print("\n⚠️  Keep this running! Disconnecting will clear the panels.\n")

    # Connect to display using adapter
    await display_adapter.connect()
    print(f"🔗 Connected to display via {adapter_type}!")

    # Initialize panels
    await display_adapter.power_on()

    # Import data and rendering modules (lazy import to avoid dependency issues)
    from core.data import (
        fetch_all_games, get_league_letter,
        fetch_current_weather, fetch_hourly_forecast, fetch_daily_forecast,
        fetch_stock_quotes
    )
    from core.rendering import (
        render_scoreboard, render_weather, render_weather_bottom_panel,
        render_clock_with_weather_split, render_stocks
    )

    try:
            
            # State tracking
            current_mode = None
            last_mode_switch = datetime.now()
            last_sports_check = datetime.now()
            last_weather_fetch = None
            
            # Sports state
            games = []
            prev_games_snapshot = None  # Store previous game states for comparison
            last_sports_render = None  # Track when we last rendered sports
            
            # Weather state
            current_weather = None
            weather_forecasts = None
            prev_current_weather = None
            prev_weather_forecasts = None
            last_weather_render = None  # Track when we last rendered weather
            
            # Clock state
            last_clock_weather_render = None  # Track when we last rendered clock+weather
            
            # Stocks state
            stock_quotes = []
            prev_stock_quotes = None
            last_stocks_check = datetime.min  # Initialize to past so it fetches immediately
            last_stocks_render = None  # Track when we last rendered stocks
            
            # Cycle state (for mode cycling)
            cycle_index = 0  # Current index in DISPLAY_CYCLE_MODES
            cycle_mode = DISPLAY_CYCLE_MODES[cycle_index]  # Start with first configured mode
            
            while True:
                now = datetime.now()
                
                # ========== CHECK FOR SPORTS (only if in cycle or priority enabled) ==========
                should_check_sports = (
                    DisplayMode.SPORTS in DISPLAY_CYCLE_MODES and
                    DISPLAY_SPORTS_PRIORITY
                )
                
                if should_check_sports and (now - last_sports_check).total_seconds() >= SPORTS_CHECK_INTERVAL:
                    print(f"\n🔍 Checking for games... ({now.strftime('%I:%M:%S %p')})")
                    try:
                        games = await fetch_all_games()
                        last_sports_check = now
                        
                        # Debug: show game states
                        print(f"  Found {len(games)} games")
                        for game in games[:5]:  # Show first 5
                            print(f"  📋 {game['away']} @ {game['home']}: state={game.get('state', 'unknown')}")
                    except Exception as e:
                        print(f"  ⚠️  Error fetching games: {e}")
                        games = []
                
                # Determine target mode based on configuration
                has_live_sports = should_check_sports and should_show_sports(games)
                
                # Sports priority logic (only if sports is in cycle AND priority enabled)
                if (DISPLAY_SPORTS_PRIORITY and 
                    DisplayMode.SPORTS in DISPLAY_CYCLE_MODES and 
                    has_live_sports):
                    # Priority mode: show sports when live games detected
                    target_mode = DisplayMode.SPORTS
                    print(f"  🏀 Live sports detected - switching to sports priority mode")
                else:
                    # Cycle through configured modes
                    time_since_switch = (now - last_mode_switch).total_seconds()
                    if time_since_switch >= DISPLAY_CYCLE_SECONDS:
                        # Move to next mode in cycle
                        cycle_index = (cycle_index + 1) % len(DISPLAY_CYCLE_MODES)
                        cycle_mode = DISPLAY_CYCLE_MODES[cycle_index]
                        last_mode_switch = now
                        print(f"  ⏭️  Cycling to: {cycle_mode}")
                    
                    target_mode = cycle_mode
                
                print(f"  Current mode: {current_mode}, Target mode: {target_mode}")
                
                # ========== MODE SWITCH ==========
                if target_mode != current_mode:
                    print(f"\n🔄 Switching mode: {current_mode} → {target_mode}")
                    
                    # ALWAYS clear screen when switching modes to ensure clean slate
                    await display_adapter.clear_screen()
                    
                    current_mode = target_mode
                    
                    # Reset mode-specific state when entering new mode
                    if target_mode == DisplayMode.SPORTS:
                        prev_games_snapshot = None
                
                # ========== RENDER CURRENT MODE ==========
                if current_mode == DisplayMode.SPORTS:
                    # Filter for live/recent games
                    display_games = []
                    for game in games:
                        state = game.get("state", "")
                        if state in ["inProgress", "in", "post", "completed", "final"]:
                            display_games.append(game)
                    
                    # Prioritize live games: if any live games exist, only show those
                    display_games = filter_live_games(display_games)
                    
                    if not display_games:
                        print("📭 No games to display - skipping to next mode")
                        # Skip to next mode in cycle
                        cycle_index = (cycle_index + 1) % len(DISPLAY_CYCLE_MODES)
                        cycle_mode = DISPLAY_CYCLE_MODES[cycle_index]
                        last_mode_switch = now
                        current_mode = None  # Force mode switch
                        continue
                    
                    # Create game snapshot for comparison
                    current_snapshot = [(g['home'], g['away'], g['home_score'], g['away_score'], 
                                        g.get('period', ''), g.get('clock', ''), g.get('state', '')) 
                                       for g in display_games]
                    
                    # Check if we need to render (data changed OR periodic refresh needed)
                    data_changed = current_snapshot != prev_games_snapshot
                    needs_refresh = (last_sports_render is None or 
                                   (now - last_sports_render).total_seconds() >= DISPLAY_SPORTS_REFRESH_INTERVAL)
                    
                    if data_changed or needs_refresh:
                        # Render scoreboard as image
                        if data_changed:
                            print("🏀 Rendering sports scoreboard (data changed)...")
                        else:
                            print("🔄 Refreshing sports display (keeping PNG alive)...")
                        
                        print(f"  Games to display: {len(display_games)}")
                        for g in display_games[:2]:
                            print(f"    {g['away']} {g['away_score']} @ {g['home']} {g['home_score']}")
                        
                        scoreboard_img = render_scoreboard(display_games, width=display_adapter.display_width, height=display_adapter.display_height)
                        
                        # Upload as PNG - DON'T clear first (screen was already cleared during mode switch)
                        await display_adapter.upload_image(scoreboard_img, clear_first=False)
                        print("✅ Scoreboard displayed!")
                        
                        # Update state
                        prev_games_snapshot = current_snapshot
                        last_sports_render = now
                
                elif current_mode == DisplayMode.CLOCK:
                    # Custom themed clock (top) + weather (bottom) rendered as PNG!
                    
                    # Fetch weather if needed
                    if last_weather_fetch is None or (now - last_weather_fetch).total_seconds() >= WEATHER_CHECK_INTERVAL:
                        print(f"🌤️ Fetching weather for clock display ({WEATHER_FORECAST_MODE} forecast)...")
                        current_weather = await fetch_current_weather()
                        if WEATHER_FORECAST_MODE == "daily":
                            weather_forecasts = await fetch_daily_forecast()
                        else:
                            weather_forecasts = await fetch_hourly_forecast()
                        last_weather_fetch = now
                    
                    # Check if we need to render/refresh (clock updates every minute, or periodic PNG refresh)
                    needs_refresh = (last_clock_weather_render is None or 
                                   (now - last_clock_weather_render).total_seconds() >= DISPLAY_CLOCK_REFRESH_INTERVAL)
                    
                    if needs_refresh and current_weather:
                        if last_clock_weather_render is None:
                            print(f"🕐 Rendering themed clock + weather (theme: {CLOCK_THEME})...")
                        else:
                            print("🔄 Refreshing clock + weather display...")
                        
                        # Render full image: clock (top half) + weather (bottom half)
                        clock_weather_img = render_clock_with_weather_split(
                            current_weather, weather_forecasts,
                            total_width=display_adapter.display_width,
                            total_height=display_adapter.display_height,
                            theme=CLOCK_THEME, hour24=CLOCK_24H
                        )
                        
                        # Upload as PNG
                        await display_adapter.upload_image(clock_weather_img, clear_first=False)
                        
                        if last_clock_weather_render is None:
                            print(f"✅ Themed clock + weather displayed!")
                        
                        last_clock_weather_render = now
                
                elif current_mode == DisplayMode.WEATHER:
                    # Fetch weather if needed
                    if last_weather_fetch is None or (now - last_weather_fetch).total_seconds() >= WEATHER_CHECK_INTERVAL:
                        print(f"🌤️ Fetching weather data ({WEATHER_FORECAST_MODE} forecast)...")
                        current_weather = await fetch_current_weather()
                        if WEATHER_FORECAST_MODE == "daily":
                            weather_forecasts = await fetch_daily_forecast()
                        else:
                            weather_forecasts = await fetch_hourly_forecast()
                        last_weather_fetch = now
                    
                    # Check if weather changed or needs refresh
                    weather_changed = (
                        prev_current_weather != current_weather or
                        prev_weather_forecasts != weather_forecasts
                    )
                    needs_refresh = (last_weather_render is None or 
                                   (now - last_weather_render).total_seconds() >= DISPLAY_WEATHER_REFRESH_INTERVAL)
                    
                    if weather_changed or needs_refresh:
                        # Render weather as image
                        if weather_changed:
                            print("🌤️ Rendering weather (data changed)...")
                        else:
                            print("🔄 Refreshing weather display (keeping PNG alive)...")
                        
                        if current_weather:
                            weather_img = render_weather(current_weather, weather_forecasts, width=display_adapter.display_width, height=display_adapter.display_height)
                            
                            # Upload as PNG - DON'T clear first (screen was already cleared during mode switch)
                            await display_adapter.upload_image(weather_img, clear_first=False)
                            print("✅ Weather displayed!")
                        
                        prev_current_weather = current_weather.copy() if current_weather else None
                        prev_weather_forecasts = weather_forecasts.copy() if weather_forecasts else None
                        last_weather_render = now
                
                elif current_mode == DisplayMode.STOCKS:
                    # Stock market display
                    
                    # Fetch stocks if needed
                    if (now - last_stocks_check).total_seconds() >= STOCKS_CHECK_INTERVAL:
                        print(f"📈 Fetching stock quotes... ({now.strftime('%I:%M:%S %p')})")
                        try:
                            stock_quotes = await fetch_stock_quotes()
                            last_stocks_check = now
                        except Exception as e:
                            print(f"  ⚠️  Error fetching stocks: {e}")
                            stock_quotes = []
                    
                    if not stock_quotes:
                        print("📭 No stock data to display - skipping to next mode")
                        # Skip to next mode in cycle
                        cycle_index = (cycle_index + 1) % len(DISPLAY_CYCLE_MODES)
                        cycle_mode = DISPLAY_CYCLE_MODES[cycle_index]
                        last_mode_switch = now
                        current_mode = None  # Force mode switch
                        continue
                    
                    # Create stock snapshot for comparison
                    current_snapshot = [(q['symbol'], q['price'], q['change_percent']) for q in stock_quotes]
                    
                    # Check if we need to render (data changed OR periodic refresh needed)
                    data_changed = current_snapshot != prev_stock_quotes
                    needs_refresh = (last_stocks_render is None or 
                                   (now - last_stocks_render).total_seconds() >= DISPLAY_STOCKS_REFRESH_INTERVAL)
                    
                    if data_changed or needs_refresh:
                        # Render stocks as image
                        if data_changed:
                            print("📈 Rendering stock quotes (data changed)...")
                        else:
                            print("🔄 Refreshing stock display (keeping PNG alive)...")
                        
                        print(f"  Quotes: {', '.join([q['symbol'] for q in stock_quotes])}")
                        
                        stocks_img = render_stocks(stock_quotes, width=display_adapter.display_width, height=display_adapter.display_height)
                        
                        # Upload as PNG - DON'T clear first (screen was already cleared during mode switch)
                        await display_adapter.upload_image(stocks_img, clear_first=False)
                        print("✅ Stocks displayed!")
                        
                        # Update state
                        prev_stock_quotes = current_snapshot
                        last_stocks_render = now
                
                # Wait before next check
                await asyncio.sleep(MODE_CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down gracefully...")
    except Exception as e:
        print(f"\n❌ Error in main loop: {e}")
        import traceback
        traceback.print_exc()
        print("\n⚠️  Keeping connection open, will retry...")
    finally:
        # Ensure we disconnect the adapter
        try:
            await display_adapter.disconnect()
            print("🔌 Disconnected from display")
        except Exception as e:
            print(f"⚠️  Error disconnecting: {e}")


if __name__ == "__main__":
    asyncio.run(main())

