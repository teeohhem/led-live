# Setup Guide

Get your LED panel display running in 5 minutes!

## Prerequisites

- **Python 3.7+**
- **Two 64x20 LED panels** (Bluetooth LE compatible)
- **OpenWeatherMap API key** (free at https://openweathermap.org/api)
- **BLE scanner app** to find your panel addresses

## Step 1: Clone and Install

```bash
git clone <your-repo-url>
cd led_panel
pip install -r requirements.txt
```

**Dependencies:**
- `bleak` - BLE communication
- `pillow` - Image rendering
- `httpx` - HTTP requests
- `yfinance` - Stock market data (optional)

## Step 2: Find Your Panel BLE Addresses

Use a BLE scanner app:

| Platform | Recommended App |
|----------|----------------|
| **iOS** | LightBlue |
| **Android** | nRF Connect |
| **macOS** | Bluetooth Explorer (from Xcode) |
| **Linux** | `bluetoothctl` or nRF Connect |

Look for your panels and note their BLE addresses:
- Format: `12:34:56:78:9A:BC`
- Or UUID format: `12345678-9ABC-...`

## Step 3: Get Weather API Key

1. Go to https://openweathermap.org/api
2. Sign up (free tier available)
3. Create an API key
4. Copy the key

**Free tier includes:**
- 60 calls/minute
- 1,000,000 calls/month

## Step 4: Configure

Copy the example config:

```bash
cp config.env.example config.env
```

Edit `config.env` with your values:

```bash
# ========== REQUIRED ==========

# Your panel BLE addresses
BLE_ADDRESS_TOP=12:34:56:78:9A:BC
BLE_ADDRESS_BOTTOM=12:34:56:78:9A:BD

# Weather API key (get from openweathermap.org)
OPENWEATHER_API_KEY=your-api-key-here

# ========== OPTIONAL ==========

# Location
WEATHER_CITY=Detroit,US

# Teams to follow (3-letter codes)
SPORTS_NHL_TEAMS=DET
SPORTS_NBA_TEAMS=DET
SPORTS_NFL_TEAMS=DET
SPORTS_MLB_TEAMS=DET

# Stock tickers to track
STOCKS_SYMBOLS=AAPL,GOOGL,MSFT,TSLA

# Display preferences
CLOCK_THEME=stranger_things
WEATHER_FORECAST_MODE=daily
CLOCK_24H=false

# What to show
DISPLAY_SPORTS_PRIORITY=true
DISPLAY_CYCLE_MODES=clock,weather,stocks
DISPLAY_CYCLE_SECONDS=300
```

## Step 5: Run!

```bash
python display_manager.py
```

You should see:
```
🚀 Starting ALL-IN-ONE Display Manager...
📺 Display: 40x64 (2 panels stacked)
🔄 Cycle Modes: clock → weather → stocks
⏱️  Cycle Duration: 300s per mode
📈 Stocks: AAPL, GOOGL, MSFT, TSLA
🌍 Weather: Detroit,US
🕐 Clock Theme: stranger_things

⚠️  Keep this running! Disconnecting will clear the panels.

🔗 Connected to both panels!
✅ Both panels initialized
```

That's it! Your display will now:
- Show live sports when your teams play
- Display themed clock + weather
- Show stock market tickers
- Auto-cycle between modes

## Troubleshooting

### "BLE_ADDRESS_TOP not configured"

**Problem:** config.env not found or missing values

**Solution:**
```bash
# Make sure you copied the example
cp config.env.example config.env

# Edit it with your actual values
nano config.env  # or vim, code, etc.
```

### "Cannot connect to panel"

**Problem:** BLE connection failed

**Solutions:**
1. Check panels are powered on
2. Verify BLE addresses are correct (use scanner app)
3. Make sure panels are in Bluetooth range (< 10 meters)
4. Try running as root/admin:
   ```bash
   sudo python display_manager.py  # Linux/Mac
   ```
5. Check for BLE interference (other devices)
6. Restart Bluetooth on your computer

### "Weather not showing"

**Problem:** API key invalid or weather fetch failed

**Solutions:**
1. Verify API key is correct in config.env
2. Check city format: `City,CountryCode` (e.g., `Detroit,US`)
3. New API keys do not function for up to a few hours after creation
4. Test API key manually:
   ```bash
   curl "https://api.openweathermap.org/data/2.5/weather?q=Detroit,US&appid=YOUR-KEY"
   ```

### "No sports showing"

**Problem:** No games found or wrong teams

**Solutions:**
1. Check team codes in config.env (use 3-letter abbreviations)
2. Sports only show when games are live (or recently completed)
3. Check ESPN API is accessible:
   ```bash
   curl "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
   ```
4. Try test mode:
   ```bash
   SPORTS_TEST_MODE=true python display_manager.py
   ```

### "Display disappears after a few seconds"

**Problem:** PNG not refreshing frequently enough

**Solution:** Decrease refresh interval in config.env:
```bash
DISPLAY_SPORTS_REFRESH_INTERVAL=1
DISPLAY_WEATHER_REFRESH_INTERVAL=1
DISPLAY_CLOCK_REFRESH_INTERVAL=1
```

### "Stocks mode showing TypeError"

**Problem:** Python 3.14 incompatibility with yfinance/protobuf

**Solutions:**
1. Use Python 3.13 or earlier:
   ```bash
   python3.13 display_manager.py
   ```
2. Or upgrade protobuf:
   ```bash
   pip install --upgrade protobuf
   ```
3. Or skip stocks mode:
   ```bash
   DISPLAY_CYCLE_MODES=clock,weather
   ```

### "Text bleeding across panels"

**Problem:** Layout positioning issue

**Solution:** Report as bug! Include:
- Number of games displayed
- Screenshot if possible
- Console output

## Next Steps

### Add Team Logos

1. Create league folders:
   ```bash
   mkdir -p logos/nfl logos/nba logos/nhl logos/mlb
   ```

2. Add team logos (PNG format, any size):
   ```bash
   logos/nfl/DET.png
   logos/nba/DET.png
   # etc.
   ```

3. Add fallback image:
   ```bash
   logos/NOT_FOUND.png  # Shown if team logo missing
   ```

See `logos/README.md` for details.

### Create Custom Clock Theme

See [Clock Themes](clock_themes.md) for more details.

Then in config.env:
```bash
CLOCK_THEME=my_theme
```

### Follow More Teams

Edit config.env:
```bash
# Multiple teams per league (comma-separated)
SPORTS_NHL_TEAMS=DET,BOS,NYR
SPORTS_NBA_TEAMS=DET,BOS,LAL
SPORTS_NFL_TEAMS=DET,GB,KC
SPORTS_MLB_TEAMS=DET,BOS,NYY
```

### Customize Display Modes

Edit config.env:
```bash
# Show only what you want
DISPLAY_CYCLE_MODES=weather,stocks  # No clock or sports

# Or cycle through everything
DISPLAY_CYCLE_MODES=sports,clock,weather,stocks
DISPLAY_CYCLE_SECONDS=120  # 2 minutes each

# Or sports priority only
DISPLAY_SPORTS_PRIORITY=true
DISPLAY_CYCLE_MODES=clock  # Just clock when no sports
```

See [Configuration Guide](configuration.md) for all options.

## Running as a Service

### Linux (systemd)

Create `/etc/systemd/system/led-panel.service`:
```ini
[Unit]
Description=LED Panel Display
After=network.target

[Service]
Type=simple
User=YOUR_USER
WorkingDirectory=/path/to/led_panel
ExecStart=/usr/bin/python3 display_manager.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable led-panel
sudo systemctl start led-panel
sudo systemctl status led-panel
```

### macOS (launchd)

Create `~/Library/LaunchAgents/com.user.led-panel.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.led-panel</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/path/to/led_panel/display_manager.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/path/to/led_panel</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

Load:
```bash
launchctl load ~/Library/LaunchAgents/com.user.led-panel.plist
```

## Need More Help?

- **Configuration:** See [Configuration Guide](configuration.md)
- **Clock Themes:** See [Clock Themes](clock_themes.md)
- **Architecture:** See main README.md
- **Issues:** Open a GitHub issue

---

**Enjoy your display!** 🎉

