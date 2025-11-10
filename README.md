# LED Live Panel Display System

A Python-based display system featuring instant PNG rendering, themed displays, and intelligent mode switching. Supports **any LED panel** through a plugin-based adapter architecture.

## Features

- **🔌 Plugin Architecture** - Support for any LED panel via extensible adapters
- **⚡ Instant Display Updates** - PNG upload for sub-second full-frame rendering
- **🏀 Sports Scoreboards** - Live scores from Detroit teams (NHL, NBA, NFL, MLB)
  - Single game: Full-screen with team logos
  - Multiple games: Compact layouts with intelligent panel boundary handling
  - Live game priority filtering
- **📈 Stock Market Display** - Real-time stock quotes with Yahoo Finance
  - Multiple symbols support
  - Color-coded price changes (red/green)
  - Pre-market price display
- **🕐 Themed Clock** - Customizable clock themes (Stranger Things, Matrix, Classic)
  - JSON-based custom themes
- **🌤️ Weather Display** - Current conditions + forecasts (hourly or daily)
  - Temperature color coding
  - Weather icons
  - Configurable forecast mode
- **🔋 Power Management** - Scheduled on/off times
  - Automatic night-time display off
  - Configurable wake/sleep schedule
- **🔄 Intelligent Mode Switching** - Auto-switches between sports, clock, weather, and stocks

## Hardware Support

This system supports **any LED panel** through a plugin-based adapter architecture. Simply create an adapter for your hardware!

### Included Adapters

- **iPixel 20x64 LED Panels** (BLE) - Default adapter
  - Service UUID: `0000fa02-0000-1000-8000-00805f9b34fb`
  - Panel Size: 64x20 pixels per panel
  - Configuration: Dual panels stacked vertically (64x40 total)

### Adding New Hardware

Want to use different LED panels? Create a new adapter! See **[Adding New Adapters](#adding-new-adapters)** below.

**For reverse-engineering incompatible panels:**
Follow this guide to install a developer bluetooth profile to your iOS device and sniff bluetooth packets from your device manufacturer and the app that controls it:
https://www.bluetooth.com/blog/a-new-way-to-debug-iosbluetooth-applications/

## Requirements

```bash
pip install bleak pillow httpx
```

**Python**: 3.7+

## Quick Start

See the **[Setup Guide](docs/setup.md)** for detailed instructions. Quick version:

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure

Copy the example config file and fill in your values:

```bash
cp config.env.example config.env
```

Edit `config.env` with your settings:
See [configuration] docs/configuration.md for more settings.
```bash
# Your LED panel BLE addresses (find using BLE scanner app)
BLE_ADDRESS_TOP=YOUR-TOP-PANEL-BLE-ADDRESS-HERE
BLE_ADDRESS_BOTTOM=YOUR-BOTTOM-PANEL-BLE-ADDRESS-HERE

# Weather API (get free key from openweathermap.org)
OPENWEATHER_API_KEY=your-api-key-here
WEATHER_CITY=YourCity,US

# Teams to follow (comma-separated)
SPORTS_NHL_TEAMS=DET
SPORTS_NBA_TEAMS=DET,BOS
SPORTS_NFL_TEAMS=DET
SPORTS_MLB_TEAMS=DET

# Stock symbols to track (comma-separated)
STOCKS_SYMBOLS=AAPL,GOOGL,MSFT,TSLA

# Display preferences
CLOCK_THEME=stranger_things
WEATHER_FORECAST_MODE=daily
CLOCK_24H=false
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run

```bash
python display_manager.py
```

## Project Structure

```
led_panel/
├── adapters/                    # Display protocol adapters
│   ├── base.py                 # Abstract DisplayAdapter interface
│   ├── loader.py               # Dynamic adapter loading system
│   ├── adapters.json           # Adapter registry
│   └── ipixel20x64/            # iPixel 20x64 adapter (BLE)
│       ├── __init__.py
│       ├── adapter.py          # BLE adapter implementation
│       └── protocol.py         # BLE protocol handling
├── core/                       # Core business logic
│   ├── data/                   # Data fetching modules
│   │   ├── __init__.py
│   │   ├── sports_data.py      # ESPN API integration
│   │   ├── weather_data.py     # OpenWeatherMap API
│   │   └── stocks_data.py      # Yahoo Finance integration
│   └── rendering/              # Display rendering modules
│       ├── __init__.py
│       ├── sports_display_png.py   # Sports scoreboard renderer
│       ├── weather_display_png.py  # Weather display renderer
│       ├── clock_display_png.py    # Themed clock renderer
│       └── stocks_display_png.py   # Stock market renderer
├── display_manager.py          # Main application & mode coordinator
├── panel_core.py               # Display adapter management
├── fonts/                      # Font files
├── logos/                      # Team logos + weather icons
│   ├── nhl/                    # NHL team logos
│   ├── nba/                    # NBA team logos
│   ├── nfl/                    # NFL team logos
│   ├── mlb/                    # MLB team logos
│   ├── NOT_FOUND.png           # Fallback logo
│   └── *.png                   # Weather icons
├── docs/                       # Documentation
│   ├── configuration.md        # Config reference
│   ├── setup.md                # Setup guide
│   └── clock_themes.md         # Clock theme guide
├── legacy/                     # Archived code
│   ├── legacy_utils.py         # Old pixel-by-pixel rendering
│   └── README.md
├── config.env                  # Your configuration (gitignored)
├── config.env.example          # Example configuration
├── custom_themes.json          # Custom clock themes (gitignored)
└── custom_themes.json.example  # Example themes
```

## Display Modes

### Sports Mode (Priority)
- Activates when live games detected
- Single game: Full screen with logos
- Two games: One per panel (20px each)
- 3-4 games: Compact layout
- Auto-updates every 10 seconds

### Stock Market Mode
- Real-time stock quotes (no API key needed!)
- Tracks 1-4 stocks simultaneously
- Color-coded: Green (up), Red (down)
- Shows price + percent change
- Updates every 5 minutes (configurable)
- Uses Yahoo Finance data

### Clock + Weather Mode
- Top panel: Themed clock with date
- Bottom panel: Current weather + 2 forecasts
- Cycles with full weather mode every 5 minutes

### Full Weather Mode
- Current conditions
- 2-4 upcoming forecasts (hourly or daily)
- Temperature color coding:
  - Blue: ≤45°F
  - Orange: 46-60°F
  - Yellow: ≥61°F

### GIF Animation Mode ⚠️ HARDWARE-DEPENDENT
- Upload animated GIFs using iPixel-CLI windowed protocol
- **Hardware Support**: Works on 96x16 iPixel displays, NOT confirmed working on 64x20 panels
- Protocol fully implemented with ACK handling per iPixel-CLI specs

**Known Compatible Hardware:**
- ✅ 96x16 iPixel displays (per iPixel-CLI documentation)
- ❌ 64x20 dual-panel setup (tested - protocol works but no visual output)

**Implementation includes:**
- ACK-based windowed protocol (12KB windows)
- Proper CRC32 checksums
- Multi-window support for large GIFs
- Notification handling for device acknowledgments

**Usage (on compatible hardware):**
```python
from panel_core import upload_gif
await upload_gif(client, "animations/test.gif")
```

**Note**: GIF animation support varies by hardware model. If animations don't display on your device, your hardware likely doesn't support this feature. Use PNG rendering instead - it's faster and works on all models!

### Power Management
- Schedule automatic display on/off times
- Save power during night hours
- Configurable wake/sleep schedule

**Configuration:**
```bash
DISPLAY_AUTO_OFF=true
DISPLAY_OFF_TIME=23:00  # Turn off at 11 PM
DISPLAY_ON_TIME=07:00   # Turn on at 7 AM
```

**Manual control:**
```python
from panel_core import led_on, led_off
await led_off(client)  # Turn display off
await led_on(client)   # Turn display on
```

## Configuration

All sensitive settings are managed via the `config.env` file:

### Environment Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `BLE_ADDRESS_TOP` | Top panel BLE address | Required | `12:34:56:78:9A:BC` |
| `BLE_ADDRESS_BOTTOM` | Bottom panel BLE address | Required | `12:34:56:78:9A:BD` |
| `BLE_UUID_WRITE` | BLE write characteristic | `0000fa02...` | Usually no change needed |
| `OPENWEATHER_API_KEY` | OpenWeatherMap API key | Required | Get from openweathermap.org |
| `WEATHER_CITY` | City for weather | `Detroit,US` | `Boston,US` |
| `SPORTS_NHL_TEAMS` | NHL teams (comma-sep) | `DET` | `DET,BOS,NYR` |
| `SPORTS_NBA_TEAMS` | NBA teams (comma-sep) | `DET` | `DET,BOS` |
| `SPORTS_NFL_TEAMS` | NFL teams (comma-sep) | `DET` | `DET,GB` |
| `SPORTS_MLB_TEAMS` | MLB teams (comma-sep) | `DET` | `DET,BOS` |
| `SPORTS_TEST_MODE` | Pick 2 random live games | `false` | `true` (for testing) |
| `DISPLAY_SPORTS_PRIORITY` | Auto-show sports when live | `true` | `false` |
| `DISPLAY_CYCLE_MODES` | Modes to cycle through | `clock,weather` | `sports,clock`, `weather` |
| `DISPLAY_CYCLE_SECONDS` | Seconds per mode | `300` | `60`, `600` |
| `CLOCK_THEME` | Clock theme | `stranger_things` | `classic`, `matrix` |
| `WEATHER_FORECAST_MODE` | Forecast type | `daily` | `hourly` |
| `CLOCK_24H` | 24-hour format | `false` | `true` |

### Alternative: System Environment Variables

Instead of `config.env`, you can set system environment variables:

```bash
export BLE_ADDRESS_TOP="your-address-here"
export OPENWEATHER_API_KEY="your-key-here"
# ... etc
python display_manager.py
```

## Customization

### Adding Custom Clock Themes

Create `custom_themes.json` with your themes:

```bash
cp custom_themes.json.example custom_themes.json
```

Edit the file to add your custom themes:

```json
{
  "my_theme": {
    "bg_color": [0, 0, 0],
    "time_color": [255, 100, 0],
    "date_color": [200, 150, 100],
    "font_time": "./fonts/PixelOperator.ttf",
    "font_date": "./fonts/PixelOperator.ttf",
    "time_size": 16,
    "date_size": 8,
    "glow": true,
    "glow_color": [50, 20, 0]
  }
}
```

Then set in `config.env`:
```bash
CLOCK_THEME=my_theme
```

**No code changes needed!** See [Clock Themes Guide](docs/clock_themes.md) for detailed theme customization.

### Adding Team Logos

1. Create league folder: `logos/nhl/`, `logos/nba/`, etc.
2. Add PNG files: `logos/nhl/DET.png`, `logos/nba/BOS.png`, etc.
3. Logos auto-crop transparent borders and maintain aspect ratio
4. Fallback: Uses `logos/NOT_FOUND.png` if team logo missing

### Following Multiple Teams

Edit your `config.env` to follow multiple teams per league:

```bash
SPORTS_NHL_TEAMS=DET,BOS,NYR
SPORTS_NBA_TEAMS=DET,BOS,LAL
SPORTS_NFL_TEAMS=DET,GB,KC
SPORTS_MLB_TEAMS=DET,BOS,ATL
```

Teams are comma-separated. The display will show games for any of your teams.

**Important**: Team matching is **league-specific**! If you follow "ATL" in MLB (Atlanta Braves), it won't accidentally match NBA's "ATL" (Atlanta Hawks). Each league has its own team list.

### Test Mode

Want to test the sports display layouts when your teams aren't playing?

Enable test mode in `config.env`:

```bash
SPORTS_TEST_MODE=true
```

This will pick 2 random live games from any league to display, letting you:
- Test the 2-game layout with logos
- See how different teams look
- Verify your display is working
- Preview layouts before game day

Set it back to `false` for normal operation (only shows your teams).

### Customizing Display Behavior

Control what your panels show and when! See `DISPLAY_MODES.md` for full documentation.

**Default behavior (Sports Fan):**
```bash
DISPLAY_SPORTS_PRIORITY=true    # Auto-switch to sports when live
DISPLAY_CYCLE_MODES=clock,weather  # Cycle these when no sports
DISPLAY_CYCLE_SECONDS=300       # 5 minutes per mode
```

**Weather Station (no sports):**
```bash
DISPLAY_SPORTS_PRIORITY=false
DISPLAY_CYCLE_MODES=weather,clock
DISPLAY_CYCLE_SECONDS=600
```

**Clock Only:**
```bash
DISPLAY_SPORTS_PRIORITY=false
DISPLAY_CYCLE_MODES=clock
```

**Stock Market Display:**
```bash
DISPLAY_SPORTS_PRIORITY=false
DISPLAY_CYCLE_MODES=stocks,clock
STOCKS_SYMBOLS=AAPL,GOOGL,MSFT,TSLA,SPY
STOCKS_CHECK_INTERVAL=300
```

**All Modes Rotation:**
```bash
DISPLAY_SPORTS_PRIORITY=false
DISPLAY_CYCLE_MODES=stocks,sports,clock,weather
DISPLAY_CYCLE_SECONDS=120
```

**Key Points:**
- When `DISPLAY_SPORTS_PRIORITY=true`, sports takes over during live games
- When `false`, sports is treated like any other mode in the cycle
- Modes cycle automatically after `DISPLAY_CYCLE_SECONDS`
- Valid modes: `stocks`, `sports`, `clock`, `weather`
- See `DISPLAY_MODES.md` for more examples and details

## API Integration

### Yahoo Finance / yfinance (Free)
- Real-time stock quotes (15-20 min delay)
- **No API key required**
- **No sign-up needed**
- **No rate limits** (reasonable use)
- Stocks, ETFs, indices, crypto
- Python library: `yfinance`

### ESPN API (Free)
- Sports scores and live game data
- No API key required
- Endpoints: NHL, NBA, NFL, MLB scoreboards

### OpenWeatherMap API (Free tier)
- Current weather
- Hourly and daily forecasts
- Free tier: 60 calls/minute
- Sign up: https://openweathermap.org/api

## PNG Rendering

The system uses PNG upload for instant display updates (vs. slow pixel-by-pixel rendering):

```python
from PIL import Image, ImageDraw
from panel_core import upload_png

# Create image
img = Image.new('RGB', (64, 40), (0, 0, 0))
draw = ImageDraw.Draw(img)

# Draw content
draw.text((10, 5), "Hello", fill=(255, 0, 0), font=font)

# Upload instantly
await upload_png(client, img)
```

Benefits:
- **100x faster** than pixel-by-pixel (< 1 second vs. 10-60 seconds)
- Full PIL features (images, transparency, gradients)
- No timing issues
- Dual-panel aware (auto-splits 64x40 images)

## Architecture

### Core Components

**adapters/**
- **base.py**: Abstract `DisplayAdapter` interface for all hardware
- **loader.py**: Dynamic adapter loading and registry management
- **adapters.json**: Registry of available adapters
- **ipixel20x64/**: iPixel BLE adapter implementation

**core/**
- **data/**: Data fetching modules (sports, weather, stocks APIs)
- **rendering/**: Display rendering modules (PNG generation)

**panel_core.py**
- Display adapter lifecycle management
- Global adapter state coordination

**display_manager.py**
- Mode coordinator and switcher
- Sports/clock/weather cycle logic
- Live game detection
- Automatic mode priorities

### Plugin Architecture

The system uses a plugin-based adapter architecture that separates **hardware communication** from **content rendering**:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data APIs     │ -> │  Content        │ -> │  Display        │
│   (ESPN, Yahoo, │    │  Rendering      │    │  Adapter        │
│    Weather)     │    │  (PIL Images)   │    │  (BLE/WiFi/etc) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

**Benefits:**
- **Hardware Independence**: Add support for any LED panel by creating a new adapter
- **Protocol Flexibility**: Support BLE, WiFi, USB, serial, or any communication method
- **Content Portability**: Same rendering logic works on all hardware
- **Easy Extension**: No core changes needed for new hardware support

### Display Pipeline

```
Data APIs → Render to PIL Image → Adapter Protocol → Hardware Display!
```

## Adding New Adapters

Want to use different LED panels? Create a new adapter! The system is designed to be easily extensible.

### Step 1: Create Adapter Directory

```bash
mkdir adapters/your_panel_name
```

### Step 2: Implement the Adapter

Create `adapters/your_panel_name/adapter.py`:

```python
from ..base import DisplayAdapter, ConnectionError, UploadError

class YourPanelAdapter(DisplayAdapter):
    def __init__(self):
        self.connection = None

    async def connect(self) -> None:
        """Establish connection to your panels"""
        try:
            # Your connection logic here
            # e.g., BLE, WiFi, USB, serial, etc.
            self.connection = "your_connection_object"
        except Exception as e:
            raise ConnectionError(f"Failed to connect: {e}")

    async def disconnect(self) -> None:
        """Close connection"""
        if self.connection:
            # Your disconnect logic
            self.connection = None

    async def upload_image(self, image, clear_first=False) -> None:
        """Upload PIL Image to your panels"""
        if not self.connection:
            raise ConnectionError("Not connected")

        try:
            # Convert PIL Image to your panel format
            # Send via your protocol (BLE, WiFi, etc.)
            pass
        except Exception as e:
            raise UploadError(f"Upload failed: {e}")

    async def clear_screen(self) -> None:
        """Clear the display"""
        # Send clear command via your protocol
        pass

    async def power_on(self) -> None:
        """Turn display on"""
        # Send power-on command
        pass

    async def power_off(self) -> None:
        """Turn display off"""
        # Send power-off command
        pass

    @property
    def display_width(self) -> int:
        """Return your panel width"""
        return 64  # Adjust for your hardware

    @property
    def display_height(self) -> int:
        """Return your panel height"""
        return 32  # Adjust for your hardware

    @property
    def is_connected(self) -> bool:
        """Check connection status"""
        return self.connection is not None

    async def get_info(self) -> dict:
        """Return adapter information"""
        return {
            "adapter_type": "your_panel_name",
            "device_count": 1,
            "panel_width": self.display_width,
            "panel_height": self.display_height,
            "total_width": self.display_width,
            "total_height": self.display_height,
            "protocol": "Your Protocol",
            "features": ["png_upload", "fast_refresh"]
        }
```

### Step 3: Create Protocol Module (Optional)

If you have complex protocol logic, create `adapters/your_panel_name/protocol.py` to separate concerns.

### Step 4: Register the Adapter

Add to `adapters.json`:

```json
{
  "adapters": {
    "your_panel_name": {
      "name": "Your Panel Brand/Model",
      "module": "adapters.your_panel_name.adapter",
      "class": "YourPanelAdapter",
      "description": "Description of your panels",
      "default": false
    }
  }
}
```

### Step 5: Use Your Adapter

Use programmatically by passing the adapter to the main function:

```python
from adapters import get_adapter
from display_manager import main

# Get your custom adapter
adapter = get_adapter('your_panel_name')

# Run with your adapter
await main(display_adapter=adapter)
```

### Adapter Interface Requirements

Your adapter must implement these methods:
- `connect()` / `disconnect()` - Connection management
- `upload_image(image, clear_first)` - Display PIL images
- `clear_screen()` - Clear display
- `power_on()` / `power_off()` - Power management
- Properties: `display_width`, `display_height`, `is_connected`
- `get_info()` - Return adapter metadata

### Example Adapters

- **BLE**: `adapters/ipixel20x64/` - iPixel BLE panels
- **WiFi**: Create `adapters/wifi_panel/` for WiFi-connected displays
- **USB**: Create `adapters/usb_panel/` for USB-connected displays
- **Serial**: Create `adapters/serial_panel/` for serial-connected displays

The rendering system automatically adapts to your panel dimensions!

## Performance

- **Full screen update**: < 1 second
- **Sports refresh**: Every 10 seconds (during live games)
- **Weather refresh**: Every 30 minutes
- **Clock updates**: Every 2 seconds (for PNG persistence)
- **BLE communication**: Chunked for reliability

## Troubleshooting

### Display shows briefly then disappears
- PNGs need periodic refresh (every 2 seconds)
- This is handled automatically by the system

### Garbled or missing text
- Check BLE addresses are correct
- Ensure panels are powered on and in range
- Try clearing panels: `await clear_screen_completely(client)`

### Sports not showing
- Verify your teams in `sports_data.py`
- Check ESPN API is accessible
- Ensure games are actually live

### Weather not updating
- Verify OpenWeatherMap API key
- Check city name format: "City,CountryCode"
- Free tier limits: 60 calls/minute

## Legacy Code

Old pixel-by-pixel rendering code has been archived to `legacy/`:
- Preserved for reference
- Not used in modern system
- See `legacy/README.md` for migration guide

## Contributing

Contributions welcome! Areas of interest:

### 🎨 Content & Themes
- New clock themes (`custom_themes.json`)
- Additional team logos (`logos/` directory)
- Weather icons and graphics

### 🔌 Hardware Support
- **New LED Panel Adapters** - See [Adding New Adapters](#adding-new-adapters)
- Support for different panel sizes and configurations
- Protocol implementations (BLE, WiFi, USB, serial)

### ⚡ Performance & Features
- Performance optimizations
- New display modes (animations, special effects)
- API integrations (new sports leagues, data sources)

### 🛠️ Development
- Bug fixes and improvements
- Documentation updates
- Testing and CI improvements

## License

MIT License - feel free to use and modify!

## Credits

- Reverse-engineered BLE protocol via packet sniffing
- PNG upload discovered through iOS app analysis
- Built with love for displaying Detroit sports!

## Documentation

- **[Setup Guide](docs/setup.md)** - Get started in 5 minutes
- **[Configuration Guide](docs/configuration.md)** - Complete configuration reference
- **[Clock Themes Guide](docs/clock_themes.md)** - Create custom clock themes
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and changes

### Additional Resources
- `legacy/README.md` - Historical context and archived code
- `logos/README.md` - Team logo organization guide

## Support

For issues or questions:
1. **First steps:** See [Setup Guide](docs/setup.md) for troubleshooting
2. **Configuration:** See [Configuration Guide](docs/configuration.md)
3. **Issues/Features:** Open a GitHub issue
4. **Architecture:** Check code comments and module docstrings

---

**Note**: This project is not affiliated with any LED panel manufacturer. It's a community-driven effort to create awesome displays!

