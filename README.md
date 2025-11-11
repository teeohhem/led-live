# LED Live Panel Display System

A Python-based display system for LED matrix panels for showing live sports scores, weather, clock, and more. It comes out of the box with support for most iPixel displays (any size). Feel free to contribute support for your adapter!

## ✨ Key Features

- **🔌 Plugin Architecture** - Support for any LED panel via extensible adapters
- **⚡ Instant Display Updates** - PNG upload for sub-second full-frame rendering
- **🏀 Sports Scoreboards** - Live scores (NHL, NBA, NFL, MLB)
- **📈 Stock Market Display** - Real-time quotes via Yahoo Finance
- **🕐 Themed Clock** - Customizable themes with glow effects
- **🌤️ Weather Display** - Current conditions + forecasts
- **🔋 Power Management** - Scheduled on/off times
- **🔄 Intelligent Mode Switching** - Auto-switches between modes
- **🎬 GIF Animations** - Frame-by-frame animation support

## 🚀 Quick Start

**1. Install dependencies:**
```bash
pip install -r requirements.txt
```

**2. Set up configuration:**
```bash
cp config.yml.example config.yml
# Edit config.yml with your panel addresses and settings
```

**3. Run:**
```bash
python3 display_manager.py
```

👉 **[Full Quick Start Guide](docs/quick-start.md)**

## 📖 Documentation

- **[Features Guide](docs/features.md)** - Detailed feature overview
- **[Configuration Guide](docs/configuration.md)** - All configuration options
- **[Quick Start](docs/quick-start.md)** - 5-minute setup
- **[Architecture](docs/architecture.md)** - System design overview
- **[Display Modes](docs/display-modes.md)** - How each mode works
- **[Creating Adapters](docs/adapters.md)** - Support new hardware
- **[Troubleshooting](docs/troubleshooting.md)** - Common issues

## 🔌 Hardware Support

### Included
- **iPixel LED Panels** (BLE) - Default adapter
  - Panel Size: Configurable (64x20 default, supports 64x32, 64x64, 32x16, 20x20, etc.)
  - Support: Single or multiple panels (1, 2, 3, 4+)
  - Connection: Bluetooth Low Energy

### Add Your Own
Create an adapter for any LED panel type. See [Creating Adapters](docs/adapters.md).

## 📋 Requirements

- **Python**: 3.7+
- **Dependencies**: See `requirements.txt`
  - `bleak` - BLE communication
  - `pillow` - Image processing
  - `pyyaml` - Configuration
  - `httpx` - HTTP requests
  - `yfinance` - Stock data

## 📁 Project Structure

```
led_panel/
├── adapters/              # Display protocol adapters
│   ├── base.py           # DisplayAdapter interface
│   └── ipixel/      # iPixel BLE adapter
├── core/
│   ├── data/             # Data fetching (APIs)
│   └── rendering/        # PNG image generation
├── docs/                 # Comprehensive guides
├── display_manager.py    # Main application
├── config.yml            # Your configuration
└── config_loader.py      # Configuration system
```

## ⚙️ Configuration

All settings in `config.yml`:

```yaml
display:
  adapter: ipixel
  ipixel:
    ble_addresses:
      - "ADDRESS-1"
      - "ADDRESS-2"

weather:
  api_key: "openweathermap-api-key"
  city: "Detroit,US"

sports:
  teams:
    nhl: ["DET"]
    nba: ["DET"]
    nfl: ["DET"]
    mlb: ["DET"]

stocks:
  symbols: "AAPL,GOOGL,MSFT,TSLA"

display_modes:
  clock_theme: "stranger_things"
  cycle_modes: [clock, weather, stocks]
  cycle_seconds: 15
```

👉 **[Full Configuration Reference](docs/configuration.md)**

## 🎨 Display Modes

### Sports
- Live game scores
- Team logos
- Multi-game layouts
- Auto-priority when games are live

### Clock
- Multiple themes (Stranger Things, Classic, Matrix)
- Custom theme support
- Weather integration
- Glow effects

### Weather
- Current conditions
- Forecasts (hourly/daily)
- Temperature color coding
- Weather icons

### Stocks
- Real-time prices
- Color-coded changes
- Multiple symbols

👉 **[Display Modes Guide](docs/display-modes.md)**

## 🛠️ Customization

### Add Custom Clock Theme
Edit `config.yml`:
```yaml
clock_themes:
  my_theme:
    bg_color: [0, 0, 0]
    time_color: [255, 100, 0]
    glow: true
    # ... more properties
```

### Track Different Teams
```yaml
sports:
  teams:
    nhl: ["DET", "BOS", "NYR"]
    nba: ["DET", "LAL", "MIA"]
```

### Watch Different Stocks
```yaml
stocks:
  symbols: "AAPL,GOOGL,SPY,QQQ"
```

## 🔗 API Keys Required

- **OpenWeatherMap** (Weather)
  - Get free key: https://openweathermap.org/api
  - Set in `config.yml` under `weather.api_key`

- **Yahoo Finance** (Stocks)
  - Free, no key required

- **ESPN API** (Sports)
  - Free, no key required

## 📊 Multi-Panel Support

The system automatically detects and supports:
- Single panel (64×20)
- Dual panels (64×40)
- Triple panels (64×60)
- Or more!

Panel count determined by number of BLE addresses in config.

👉 **[Multi-Panel Setup](docs/multi-panel.md)**

## 🏗️ Adding New Hardware

Create an adapter for any LED panel:
1. Implement `DisplayAdapter` interface
2. Handle BLE/USB/network communication
3. Register in `adapters.json`
4. Add config section in `config.yml.example`

👉 **[Creating Adapters Guide](docs/adapters.md)**

## 🐛 Troubleshooting

Common issues and solutions in **[Troubleshooting Guide](docs/troubleshooting.md)**

Quick fixes:
- **"No panels found"** - Check BLE addresses
- **"Connection timeout"** - Ensure Bluetooth is enabled
- **"Config not found"** - Run `cp config.yml.example config.yml`

## 📝 License

See [LICENSE](LICENSE) file

## 🙏 Credits

- **Sports Data** - ESPN API
- **Weather Data** - OpenWeatherMap
- **Stock Data** - Yahoo Finance
- **Panel Hardware** - iPixel (default)
- **Python Libraries** - bleak, pillow, pyyaml, httpx, yfinance

## 📚 Learn More

- [Features Overview](docs/features.md)
- [Architecture Deep Dive](docs/architecture.md)
- [Full Configuration Reference](docs/configuration.md)
- [Quick Start Guide](docs/quick-start.md)

## ❓ Questions?

- Check the [Troubleshooting Guide](docs/troubleshooting.md)
- Read the [Configuration Guide](docs/configuration.md)
- Review [Architecture Overview](docs/architecture.md)

