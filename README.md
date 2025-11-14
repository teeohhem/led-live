# LED Live Panel Display System

A Python-based display system for LED matrix panels for showing live sports scores, weather, clock, and more. It comes out of the box with support for most iPixel displays (any size). Feel free to contribute support for your adapter!

## ✨ Key Features

- **🔌 Plugin Architecture** - Support for any LED panel via extensible adapters and layouts
- **🏀 Sports Scoreboards** - Live scores (NHL, NBA, NFL, MLB)
- **📈 Stock Market Display** - Real-time quotes via Yahoo Finance
- **🕐 Themed Clock** - Customizable themes
- **🌤️ Weather Display** - Current conditions + forecasts
- **🔋 Power Management** - Scheduled on/off times
- **🔄 Intelligent Mode Switching** - Auto-switches between modes
- **🎬 GIF Animations** - Frame-by-frame animation support
- ** Scrolling Ticker** - Display data in a ticker-style

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

## 🐛 Troubleshooting

Common issues and solutions in **[Troubleshooting Guide](docs/troubleshooting.md)**

## 📝 License

See [LICENSE](LICENSE) file

## 🙏 Credits

- **Sports Data** - ESPN API
- **Weather Data** - OpenWeatherMap
- **Stock Data** - Yahoo Finance
- **Panel Hardware** - iPixel (default)
- **Team Logos** - https://www.stickpng.com/
- **Python Libraries** - bleak, pillow, pyyaml, httpx, yfinance

## Related Projects
- [iPixel CLI](https://github.com/lucagoc/iPixel-CLI) - CLI for interacting with iPixel displays

## 📚 Learn More

- [Features Overview](docs/features.md)
- [Architecture Deep Dive](docs/architecture.md)
- [Full Configuration Reference](docs/configuration.md)
- [Quick Start Guide](docs/quick-start.md)

## ❓ Questions?

- Check the [Troubleshooting Guide](docs/troubleshooting.md)
- Read the [Configuration Guide](docs/configuration.md)
- Review [Architecture Overview](docs/architecture.md)

