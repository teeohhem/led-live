# Quick Start Guide

Get the LED panel display system up and running in 5 minutes.

## Prerequisites

- **Python** 3.7 or higher
- **LED Panel** - iPixel panels (any size - 64x20, 64x32, 64x64, etc.)
- **BLE Scanner App** - To find your panel's BLE address
- **Free API Keys** - OpenWeatherMap (for weather)

## Step 1: Install Dependencies

```bash
cd /path/to/led_panel
pip install -r requirements.txt
```

This installs:
- `bleak` - BLE communication
- `pillow` - Image processing
- `pyyaml` - Configuration management
- `httpx` - HTTP requests
- `yfinance` - Stock data

**Note:** If you get permission errors, try `pip install --user -r requirements.txt`

## Step 2: Find Your Panel BLE Addresses

Use a BLE scanner app to find your LED panel's Bluetooth address:

**iOS:**
- Download "BLE Scanner" app from App Store
- Open and scan
- Find your panel (usually shows as "iPixel" or similar)
- Note the address (looks like: `85736B96-4E4E-4EEF-B470-A351D43587BE`)

**Android:**
- Download "BLE Scanner" or "nRF Connect"
- Scan for devices
- Note the MAC address of your panels

**macOS:**
- Use `bleak-scanner` command-line tool (if installed)
- Or manually enable BLE logging

## Step 3: Create Configuration

Copy the example configuration:

```bash
cp config.yml.example config.yml
```

Edit `config.yml` and update these key sections:

### Panels
```yaml
display:
  adapter: ipixel
  ipixel:
    size_width: 64                 # Panel width (default: 64)
    size_height: 20                # Panel height (default: 20)
    ble_addresses:
      - "YOUR-PANEL-1-ADDRESS"      # Replace with your addresses
      - "YOUR-PANEL-2-ADDRESS"
```

### Weather (Optional)
```yaml
weather:
  api_key: "YOUR-API-KEY"           # Get free key from openweathermap.org
  city: "Detroit,US"                # Your city
  units: "imperial"                 # or "metric"
```

### Sports (Optional)
```yaml
sports:
  teams:
    nhl: ["DET"]                    # Your favorite teams
    nba: ["DET"]
    nfl: ["DET"]
    mlb: ["DET"]
```

### Stocks (Optional)
```yaml
stocks:
  symbols: "AAPL,GOOGL,MSFT,TSLA"   # Stock symbols to track
```

## Step 4: Test Connection

Verify everything works:

```bash
python3 -c "
from adapters import get_adapter
import asyncio

async def test():
    adapter = get_adapter('ipixel')
    await adapter.connect()
    print('✅ Connected to panels!')
    await adapter.disconnect()

asyncio.run(test())
"
```

Expected output:
```
🔗 Connecting to 2 LED panel(s)...
✅ Connected to panel 1/2
✅ Connected to panel 2/2
✅ Connected to all 2 panel(s)!
✅ Connected to panels!
```

## Step 5: Run the Application

```bash
python3 display_manager.py
```

You should see the LED panels displaying content and cycling through modes!

## Troubleshooting

### "No panels found"
- Check BLE addresses in `config.yml`
- Verify panels are powered on and in range
- Re-scan with BLE scanner app to confirm addresses

### "Connection timeout"
- Ensure Bluetooth is enabled on your computer
- Try pairing the panels with your system first
- Check panels aren't already connected to another device

### "Import error for bleak"
- Make sure you ran `pip install -r requirements.txt`
- Try `pip install --upgrade bleak`

### "No weather data"
- Verify OpenWeatherMap API key is valid
- Check internet connection
- Confirm city format: "City,CountryCode" (e.g., "Detroit,US")

### "Config.yml not found"
- Run `cp config.yml.example config.yml`
- Ensure you're in the project root directory

## Next Steps

- **Customize themes** - See [docs/configuration.md](configuration.md)
- **Add adapters** - See [docs/adapters.md](adapters.md)
- **Understand modes** - See [docs/features.md](features.md)
- **Multi-panel setup** - See [docs/multi-panel.md](multi-panel.md)

## Common Commands

```bash
# Run the application
python3 display_manager.py

# Test individual modules
python3 -c "from core.data import sports_data; print(sports_data.get_live_games())"

# Check configuration
python3 -c "from config_loader import load_config; c = load_config(); print(c.get('display.adapter'))"

# Test adapter connectivity
python3 -c "
import asyncio
from adapters import get_adapter

async def test():
    adapter = get_adapter('ipixel')
    await adapter.connect()
    print('Connected!')
    await adapter.led_on()
    await asyncio.sleep(2)
    await adapter.led_off()
    await adapter.disconnect()

asyncio.run(test())
"
```

## Getting Help

- **Configuration Issues** - See [docs/configuration.md](configuration.md)
- **Hardware Issues** - See [docs/troubleshooting.md](troubleshooting.md)
- **Feature Questions** - See [docs/features.md](features.md)

