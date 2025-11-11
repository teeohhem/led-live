# Configuration Guide

The LED Panel Display System uses YAML configuration files for easy organization and readability.

## Setup

### 1. Create Configuration File

```bash
cp config.yml.example config.yml
```

### 2. Edit `config.yml`

Update the values in `config.yml` to match your setup:

```yaml
display:
  adapter: ipixel
  ipixel:
    ble_addresses:
      - "YOUR-PANEL-1-ADDRESS"
      - "YOUR-PANEL-2-ADDRESS"
```

### 3. Install PyYAML (if not already installed)

```bash
pip install pyyaml
```

## Configuration Sections

### Display Adapter Settings

```yaml
display:
  adapter: ipixel  # Which adapter to use
  
  ipixel:
    size_width: 64      # Panel width in pixels (default: 64)
    size_height: 20     # Panel height in pixels (default: 20)
    ble_addresses:      # BLE addresses of your panels
      - "ADDRESS-1"
      - "ADDRESS-2"
    ble_uuid_write: "0000fa02-0000-1000-8000-00805f9b34fb"  # BLE UUID
```

**Panel Count:** Determined automatically by the number of BLE addresses.
- 1 address = 1 panel
- 2 addresses = 2 panels (stacked vertically)
- 3+ addresses = Multi-panel setup

**Panel Dimensions:** Configurable per adapter (default 64×20)
- `size_width`: Panel width in pixels
- `size_height`: Panel height in pixels

**Supported Sizes:**
- 64×20 - Standard iPixel (default)
- 64×32 - Tall variant
- 64×64 - Large square
- 32×16 - Small
- 20×20 - Minimal
- Any custom size supported by your panels

### Weather Settings

```yaml
weather:
  api_key: "your-openweathermap-api-key"
  city: "Detroit,US"              # Format: City,CountryCode
  units: "imperial"               # imperial or metric
  forecast_mode: "daily"          # daily or hourly
  show_icons: true                # Display weather icons
  check_interval: 1800            # Seconds (1800 = 30 min)
  refresh_interval: 2             # Seconds
```

Get a free API key from [OpenWeatherMap](https://openweathermap.org/api).

### Stocks Settings

```yaml
stocks:
  symbols: [AAPL,GOOGL,MSFT,TSLA]  # Comma-separated ticker symbols
  check_interval: 300              # Seconds (300 = 5 min)
  refresh_interval: 2              # Seconds
```

### Sports Settings

```yaml
sports:
  teams:
    nhl: ["DET"]                   # List of team abbreviations
    nba: ["DET"]
    nfl: ["DET"]
    mlb: ["DET"]
  test_mode: false                 # Use random games for testing
  check_interval: 10               # Seconds
  show_logos: true                 # Display team logos
  refresh_interval: 2              # Seconds
```

**Team Abbreviations:** Teams are league-specific, so the same abbreviation (e.g., "ATL") can refer to different teams in different leagues:
- NHL: Detroit Red Wings = "DET"
- NBA: Atlanta Hawks = "ATL"
- NFL: Atlanta Falcons = "ATL"
- MLB: Arizona Diamondbacks = "ARI"

### Display Modes

```yaml
display_modes:
  sports_priority: true            # Auto-switch to sports when games are live
  cycle_modes:                      # Modes to cycle through
    - clock
    - weather
    - stocks
  cycle_seconds: 15                 # Seconds per mode
  clock_theme: "stranger_things"    # Clock style (stranger_things, classic, matrix)
  clock_24h: false                  # 24-hour format
  mode_check_interval: 2            # Seconds
```

### Power Management

```yaml
power:
  auto_off: true                   # Automatically turn off at night
  off_time: "23:00"                # Turn off time (24-hour format)
  on_time: "07:00"                 # Turn on time (24-hour format)
```

## Finding Panel BLE Addresses

Use a Bluetooth Low Energy scanner app to find your panels' MAC addresses:

- **iOS:** Search for "BLE Scanner" app
- **Android:** Use "BLE Scanner" or similar app
- **macOS:** Use "BLE Explorer" or Terminal with `bleak-scanner`

The addresses will look like: `85736B96-4E4E-4EEF-B470-A351D43587BE`

## Migration from .env Files

If you were using `config.env`:

1. Create new `config.yml` from `config.yml.example`
2. Copy values from `config.env` to `config.yml` using the YAML structure
3. Delete or rename `config.env` (the system now uses `config.yml`)

**Before (.env):**
```
DISPLAY_ADAPTER=ipixel
BLE_ADDRESSES=ADDR1,ADDR2
WEATHER_CITY=Detroit,US
```

**After (config.yml):**
```yaml
display:
  adapter: ipixel
  ipixel:
    ble_addresses:
      - ADDR1
      - ADDR2

weather:
  city: "Detroit,US"
```

## Using Configuration in Code

```python
from config_loader import load_config

# Load configuration on startup
config = load_config()

# Get values
adapter = config.get_string("display.adapter")
addresses = config.get_list("display.ipixel.ble_addresses")
api_key = config.get_string("weather.api_key")
priority = config.get_bool("display_modes.sports_priority")
interval = config.get_int("weather.check_interval")
```

## YAML Syntax Tips

### Lists
```yaml
# Array syntax
teams: ["DET", "BOS"]

# Or block syntax
teams:
  - DET
  - BOS
```

### Strings with Colons
Use quotes if the value contains a colon:
```yaml
api_key: "12345:abcde"  # Correct
# api_key: 12345:abcde  # Wrong - YAML will interpret as a mapping
```

### Comments
```yaml
# This is a comment
setting: value  # Inline comment
```

### Nested Objects
```yaml
display:
  adapter: ipixel
  ipixel:
    setting1: value1
    setting2: value2
```

## Troubleshooting

### "PyYAML not installed"

Install it:
```bash
pip install pyyaml
```

### "config.yml not found"

Create it from the example:
```bash
cp config.yml.example config.yml
```

### Invalid YAML syntax

Check your file at [yamllint.com](http://www.yamllint.com/) or validate with:
```bash
python3 -c "import yaml; yaml.safe_load(open('config.yml'))"
```

### Values not being read

Ensure you're using the correct path with dot notation:
```python
config.get("display.adapter")      # Correct
config.get("display_adapter")      # Wrong
```
