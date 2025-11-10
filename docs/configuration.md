# Configuration Guide

Complete guide to configuring your LED Panel Display System.

## Quick Start

1. Copy the example config:
   ```bash
   cp config.env.example config.env
   ```

2. Edit `config.env` with your values:
   ```bash
   # Required
   BLE_ADDRESS_TOP=12:34:56:78:9A:BC
   BLE_ADDRESS_BOTTOM=12:34:56:78:9A:BD
   OPENWEATHER_API_KEY=your-api-key-here
   
   # Optional
   WEATHER_CITY=Detroit,US
   SPORTS_NHL_TEAMS=DET
   SPORTS_NBA_TEAMS=DET
   CLOCK_THEME=stranger_things
   ```

3. Run:
   ```bash
   python display_manager.py
   ```

## Configuration System

The system loads configuration in this order (highest priority first):

1. **System environment variables**
2. **config.env file** (git-ignored)
3. **Default values** (fallback)

This allows flexible deployment:
- Local development: Use `config.env`
- Docker/containers: Use env vars or mounted config
- CI/CD: Use secrets management

---

## Hardware Settings

### Panel Dimensions

```bash
# Physical panel size
PANEL_WIDTH=64           # Width of each panel in pixels (default: 64)
PANEL_HEIGHT=20          # Height of each panel in pixels (default: 20)
PANEL_COUNT=2            # Number of panels stacked vertically (default: 2)
```

**When to change:**
- Different panel sizes (32x16, 128x32, etc.)
- Single panel setup
- Different stacking configuration

### BLE Addresses

```bash
# BLE addresses (REQUIRED)
BLE_ADDRESS_TOP=YOUR-TOP-PANEL-ADDRESS
BLE_ADDRESS_BOTTOM=YOUR-BOTTOM-PANEL-ADDRESS

# BLE characteristic UUID (usually no change needed)
BLE_UUID_WRITE=0000fa02-0000-1000-8000-00805f9b34fb
```

**Finding your addresses:**
- Use a BLE scanner app (LightBlue on iOS, nRF Connect on Android)
- Format: `12:34:56:78:9A:BC` or `12345678-9ABC-...`

---

## API Settings

### Weather API

```bash
# OpenWeatherMap (REQUIRED for weather modes)
OPENWEATHER_API_KEY=your-api-key-here
WEATHER_CITY=Detroit,US
WEATHER_UNITS=imperial          # imperial (°F) or metric (°C)
WEATHER_CHECK_INTERVAL=1800     # Seconds between updates (default: 1800 = 30min)
```

**Getting an API key:**
1. Go to https://openweathermap.org/api
2. Sign up (free tier available)
3. Create an API key
4. Copy to config.env

**Free tier limits:** 60 calls/minute, 1,000,000 calls/month

**Recommended intervals:**
- Minimum: 600 (10 minutes)
- Default: 1800 (30 minutes)
- Maximum: 3600+ (1 hour+)

### Sports API

```bash
# ESPN API (no key required)
SPORTS_CHECK_INTERVAL=10        # Seconds between score updates (default: 10)
SPORTS_NHL_TEAMS=DET
SPORTS_NBA_TEAMS=DET
SPORTS_NFL_TEAMS=DET
SPORTS_MLB_TEAMS=DET
SPORTS_TEST_MODE=false          # Pick 2 random live games for testing
```

**Team codes:** Use 3-letter abbreviations (DET, BOS, NYR, etc.)
**Multiple teams:** Comma-separated (e.g., `DET,BOS,NYR`)

**Recommended intervals:**
- Live games: 5-15 seconds (no bandwidth limits)
- ESPN's free API has no strict rate limits

### Stock Market API

```bash
# Yahoo Finance via yfinance (no key required)
STOCKS_SYMBOLS=AAPL,GOOGL,MSFT,TSLA
STOCKS_CHECK_INTERVAL=300       # Seconds between updates (default: 300 = 5min)
```

**Symbols:** Use standard ticker symbols (e.g., AAPL, TSLA)
**Recommended interval:** 300+ seconds (market data doesn't need frequent updates)

---

## Display Behavior

### Mode Management

```bash
# What to show and when
DISPLAY_SPORTS_PRIORITY=true       # Auto-show sports when live (default: true)
DISPLAY_CYCLE_MODES=clock,weather,stocks  # Modes to cycle through
DISPLAY_CYCLE_SECONDS=300          # Seconds per mode (default: 300 = 5min)
DISPLAY_MODE_CHECK_INTERVAL=2      # How often to check for mode changes (default: 2)
```

**Valid modes:**
- `sports` - Live scores with logos
- `clock` - Themed clock + weather
- `weather` - Full weather display
- `stocks` - Stock market tickers

**How Priority Works:**

With `DISPLAY_SPORTS_PRIORITY=true`:
```
Live game detected? 
  → Yes: Show SPORTS (ignore cycle)
  → No: Cycle through DISPLAY_CYCLE_MODES
```

With `DISPLAY_SPORTS_PRIORITY=false`:
```
Always cycle through DISPLAY_CYCLE_MODES
Only show sports when it's its turn in the cycle
```

### Display Mode Examples

**Sports Fan (Default)**
```bash
DISPLAY_SPORTS_PRIORITY=true
DISPLAY_CYCLE_MODES=clock,weather
DISPLAY_CYCLE_SECONDS=300
```
Shows sports when live, otherwise cycles clock/weather every 5 minutes.

**Weather Station**
```bash
DISPLAY_SPORTS_PRIORITY=false
DISPLAY_CYCLE_MODES=weather
```
Always shows weather, never sports or clock.

**Stock Tracker**
```bash
DISPLAY_SPORTS_PRIORITY=false
DISPLAY_CYCLE_MODES=stocks,clock
DISPLAY_CYCLE_SECONDS=600
```
Cycles between stocks and clock every 10 minutes.

**Balanced Rotation**
```bash
DISPLAY_SPORTS_PRIORITY=false
DISPLAY_CYCLE_MODES=sports,clock,weather,stocks
DISPLAY_CYCLE_SECONDS=180
```
3 minutes per mode, rotates through all modes regardless of live games.

### PNG Refresh Rates

```bash
# How often to re-upload PNGs (keeps display alive)
DISPLAY_SPORTS_REFRESH_INTERVAL=2    # Seconds (default: 2)
DISPLAY_WEATHER_REFRESH_INTERVAL=2   # Seconds (default: 2)
DISPLAY_CLOCK_REFRESH_INTERVAL=2     # Seconds (default: 2)
DISPLAY_STOCKS_REFRESH_INTERVAL=2    # Seconds (default: 2)
```

**Why refresh?** PNGs don't persist indefinitely on panels. Periodic re-upload prevents disappearing displays.

**Tuning:**
- Display disappears: decrease to 1 second
- Too much BLE traffic: increase to 5 seconds

---

## Visual Preferences

### Clock Appearance

```bash
CLOCK_THEME=stranger_things     # Theme: stranger_things, classic, matrix
CLOCK_24H=false                 # 24-hour format (default: false = 12-hour)
```

**Available themes:**
- `stranger_things` - Red text, retro glow
- `classic` - Cyan/yellow, clean
- `matrix` - Green, tech aesthetic

See [Clock Themes](clock_themes.md) for creating custom themes.

### Weather Display

```bash
WEATHER_FORECAST_MODE=daily     # Forecast type: daily or hourly
WEATHER_SHOW_ICONS=true         # Show weather icons (default: true)
WEATHER_COLOR_TEMPS=true        # Color-code temperatures (default: true)
```

**Temperature colors** (when enabled):
- Blue: ≤45°F
- Orange: 46-60°F
- Yellow: ≥61°F

### Sports Display

```bash
SPORTS_SHOW_LOGOS=true          # Show team logos (default: true)
```

**Logo organization:**
- Place logos in `logos/{league}/{TEAM}.png`
- Example: `logos/nfl/DET.png`
- Fallback: `logos/NOT_FOUND.png` if team logo missing

---

## Timing & Performance

### Check Intervals

How often to fetch fresh data from APIs:

```bash
SPORTS_CHECK_INTERVAL=10        # Seconds (default: 10)
WEATHER_CHECK_INTERVAL=1800     # Seconds (default: 1800 = 30min)
STOCKS_CHECK_INTERVAL=300       # Seconds (default: 300 = 5min)
```

**Recommendations:**
- Sports: 5-15 seconds for live games
- Weather: 1800+ seconds (API limits)
- Stocks: 300+ seconds (market data frequency)

### Advanced Settings

```bash
# BLE communication
BLE_CONNECT_TIMEOUT=10          # Connection timeout in seconds
BLE_COMMAND_DELAY=0.01          # Delay between commands

# PNG upload
PNG_MAX_RETRIES=3               # Retry failed uploads
PNG_RETRY_DELAY=0.5             # Seconds between retries
```

**When to tune:**
- Connection issues: increase timeout
- Commands failing: increase command delay
- Upload errors: adjust retries

---

## Configuration Examples

### Minimal (Clock Only)

```bash
# Hardware
BLE_ADDRESS_TOP=YOUR-ADDRESS
BLE_ADDRESS_BOTTOM=YOUR-ADDRESS

# Display
DISPLAY_SPORTS_PRIORITY=false
DISPLAY_CYCLE_MODES=clock
CLOCK_THEME=classic
```

### Sports Fan (High Frequency)

```bash
# Hardware
BLE_ADDRESS_TOP=YOUR-ADDRESS
BLE_ADDRESS_BOTTOM=YOUR-ADDRESS

# Sports
SPORTS_NHL_TEAMS=DET,BOS
SPORTS_NBA_TEAMS=DET,BOS
SPORTS_CHECK_INTERVAL=5          # Update every 5 seconds
SPORTS_SHOW_LOGOS=true

# Display
DISPLAY_SPORTS_PRIORITY=true
DISPLAY_CYCLE_MODES=clock,weather
DISPLAY_CYCLE_SECONDS=180        # 3 minute cycles
```

### All Features (Balanced)

```bash
# Hardware
BLE_ADDRESS_TOP=YOUR-ADDRESS
BLE_ADDRESS_BOTTOM=YOUR-ADDRESS

# APIs
OPENWEATHER_API_KEY=your-key
WEATHER_CITY=Detroit,US
WEATHER_CHECK_INTERVAL=1800

# Sports
SPORTS_NHL_TEAMS=DET
SPORTS_NBA_TEAMS=DET
SPORTS_CHECK_INTERVAL=10

# Stocks
STOCKS_SYMBOLS=AAPL,GOOGL,MSFT,TSLA
STOCKS_CHECK_INTERVAL=300

# Display
DISPLAY_SPORTS_PRIORITY=true
DISPLAY_CYCLE_MODES=clock,weather,stocks
DISPLAY_CYCLE_SECONDS=300
CLOCK_THEME=stranger_things
WEATHER_FORECAST_MODE=daily
```

---

## Validation

The system validates configuration on startup:

✅ **Valid configuration:**
```
🚀 Starting ALL-IN-ONE Display Manager...
📺 Display: 40x64 (2 panels stacked)
🔄 Cycle Modes: clock → weather → stocks
⏱️  Cycle Duration: 300s per mode
📈 Stocks: AAPL, GOOGL, MSFT, TSLA
```

❌ **Invalid configuration:**
```
❌ Invalid display modes in config: foo, bar
   Valid modes: sports, clock, weather, stocks
```

---

## Troubleshooting

### "BLE_ADDRESS_TOP not configured"
- Make sure you copied `config.env.example` to `config.env`
- Fill in your actual BLE addresses

### "Cannot connect to panel"
- Check panels are powered on
- Verify BLE addresses are correct
- Ensure panels are in Bluetooth range
- Try running as root/admin if needed

### "Weather not showing"
- Verify API key is valid
- Check city format: "City,CountryCode"
- Check you're within free tier limits

### "No sports showing"
- Verify team codes in `config.env`
- Sports only show when games are live (or completed if no live games)
- Check ESPN API is accessible

### "Display disappears"
- Decrease refresh interval (e.g., `DISPLAY_*_REFRESH_INTERVAL=1`)
- Check BLE connection stability

### "Too slow / laggy"
- Reduce check intervals
- Increase PNG refresh intervals

---

## Docker / Container Deployment

### Option 1: Mount config.env
```bash
docker run -v $(pwd)/config.env:/app/config.env led-panel
```

### Option 2: Use environment variables
```bash
docker run \
  -e BLE_ADDRESS_TOP=12:34:56:78:9A:BC \
  -e BLE_ADDRESS_BOTTOM=12:34:56:78:9A:BD \
  -e OPENWEATHER_API_KEY=your-key \
  led-panel
```

### Option 3: docker-compose
```yaml
services:
  led-panel:
    build: .
    env_file:
      - config.env
```

---

## Security Best Practices

1. **Never commit secrets**
   - `config.env` is git-ignored by default
   - Use `config.env.example` as template only

2. **Use environment variables in production**
   - System env vars or secret management
   - Avoid hardcoding in code

3. **Rotate API keys periodically**
   - Especially if sharing code or logs

4. **Check .gitignore**
   - Ensure `config.env` is listed
   - Verify no secrets in git history

---

## Need Help?

- **Setup issues:** See [Setup Guide](setup.md)
- **Clock themes:** See [Clock Themes](clock_themes.md)
- **Code architecture:** See main README.md
- **Open an issue:** GitHub issues for bugs/features

---

**Next:** [Clock Themes Guide](clock_themes.md) | [Setup Guide](setup.md)

