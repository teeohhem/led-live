# LED Panel Features

## Display Modes

The system intelligently switches between multiple display modes:

### 🏀 Sports Mode (Priority)
Live scores and game information from your favorite teams:
- **Single Game View** - Full-screen with team logos
- **Multiple Games** - Compact layouts that adapt to panel count
- Intelligent panel boundary handling for multi-panel displays
- Live game detection and auto-switch
- Supports: NHL, NBA, NFL, MLB

### 🕐 Clock Mode
Multiple customizable clock themes:
- **Stranger Things** - Retro VHS aesthetic
- **Classic** - Simple, elegant design
- **Matrix** - Digital cascading effect
- **Custom Themes** - Create your own via YAML config
- Glow effects and color customization
- Weather integration on clock display

### 🌤️ Weather Mode
Current conditions and forecasts:
- Real-time weather data via OpenWeatherMap
- Temperature color coding (blue=cold, red=hot)
- Weather icons (sun, clouds, rain, snow, etc.)
- Hourly or daily forecast modes
- Configurable city and units (imperial/metric)

### 📈 Stocks Mode
Real-time stock market data:
- Multiple stock symbols support
- Color-coded price changes (green=up, red=down)
- Pre-market price display
- Yahoo Finance integration
- Adaptive layouts (1-4 stocks)

## Mode Switching

The system automatically cycles through enabled modes:
- **Sports Priority** - Automatically shows sports when games are live
- **Cycle Interval** - Time each mode displays (default: 15 seconds)
- **Configurable Modes** - Choose which modes to enable

Example cycling: Sports → Clock → Weather → Stocks → repeat

## Power Management

Scheduled display on/off:
- **Auto Off** - Disable at night to save power
- **Off Time** - When to turn off (24-hour format)
- **On Time** - When to turn on
- Battery-friendly operation

## Customization

### Clock Themes
Define custom themes in `config.yml`:
```yaml
clock_themes:
  my_theme:
    bg_color: [0, 0, 0]              # Background (RGB)
    time_color: [255, 100, 0]        # Time display (RGB)
    date_color: [200, 150, 100]      # Date display (RGB)
    font_time: "./fonts/PixelOperator.ttf"
    font_date: "./fonts/PixelOperator.ttf"
    time_size: 16
    date_size: 8
    glow: true                       # Enable glow
    glow_color: [50, 20, 0]          # Glow color (RGB)
```

### Team Selection
Track teams across all major leagues:
```yaml
sports:
  teams:
    nhl: ["DET", "BOS", "NYR"]
    nba: ["DET", "BOS", "LAL"]
    nfl: ["DET", "BOS", "KC"]
    mlb: ["DET", "BOS", "NYY"]
```

### Stock Symbols
Watch any stock symbols:
```yaml
stocks:
  symbols: "AAPL,GOOGL,MSFT,TSLA,SPY,QQQ"
```

### Display Preferences
```yaml
display_modes:
  sports_priority: true              # Auto-switch to sports
  cycle_modes: [clock, weather, stocks]
  cycle_seconds: 15                  # Duration per mode
  clock_theme: "stranger_things"
  clock_24h: false                   # 12-hour format
```

## Performance

- **⚡ Instant Updates** - PNG rendering for sub-second display updates
- **🔋 Efficient** - Minimal BLE traffic, smart refresh intervals
- **📡 Multi-Panel** - Automatic panel boundary handling
- **🎯 Flexible Panel Sizes** - Configurable dimensions (64x20, 64x32, 64x64, etc.)

## Animation Support

- **GIF Animations** - Smooth frame-by-frame playback
- **Custom Animations** - Create your own GIFs
- **Panel Targeting** - Send animations to specific panels
- **Timing** - Respects frame delays and timing

## API Integrations

- **ESPN API** - Sports scores and live games
- **OpenWeatherMap** - Weather data (free API key)
- **Yahoo Finance** - Real-time stock quotes
- All configured via `config.yml`

