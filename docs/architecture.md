# System Architecture

High-level overview of how the LED panel system is organized.

## Component Overview

```
┌─────────────────────────────────────────────────────────┐
│                   display_manager.py                      │
│              (Main Application & Coordinator)             │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────┬──────────────┐
        ▼            ▼            ▼              ▼
   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────────┐
   │ Sports  │ │ Clock   │ │ Weather │ │   Stocks     │
   │ Renderer│ │ Renderer│ │Renderer │ │  Renderer    │
   └────┬────┘ └────┬────┘ └────┬────┘ └──────┬───────┘
        │           │           │              │
        └───────────┼───────────┼──────────────┘
                    ▼
        ┌─────────────────────────────┐
        │  core/rendering/             │
        │  (PNG Generation)            │
        └────────────┬────────────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
   ┌─────────┐ ┌─────────┐ ┌─────────┐
   │ Sports  │ │ Weather │ │ Stocks  │
   │  Data   │ │  Data   │ │  Data   │
   │ (APIs)  │ │ (APIs)  │ │ (APIs)  │
   └─────────┘ └─────────┘ └─────────┘
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
   ┌─────────────────────┐  ┌──────────────────┐
   │  panel_core.py      │  │ config_loader.py │
   │  (Adapter Manager)  │  │ (Configuration)  │
   └────────┬────────────┘  └──────────────────┘
            │
     ┌──────┴──────┐
     ▼             ▼
┌────────────┐ ┌────────────┐
│ Adapter    │ │ Adapter    │
│ Interface  │ │ Registry   │
│ (base.py)  │ │ (loader.py)│
└────────────┘ └─────┬──────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
   ┌─────────┐ ┌─────────┐ ┌─────────┐
   │ iPixel  │ │ Future  │ │ Future  │
   │20x64    │ │Adapter 1│ │Adapter 2│
   │(BLE)    │ │         │ │         │
   └────┬────┘ └─────────┘ └─────────┘
        │
        ▼
   ┌──────────────────────────┐
   │  BLE Protocol            │
   │  (Hardware Interface)    │
   └──────────────────────────┘
        │
        ▼
   ┌──────────────────────────┐
   │  LED Panels (Hardware)   │
   └──────────────────────────┘
```

## Layer Breakdown

### 1. **Application Layer** (`display_manager.py`)
- Main orchestrator
- Coordinates mode switching
- Refreshes displays at configured intervals
- Handles system lifecycle (startup, shutdown)
- Implements intelligent mode priority logic

### 2. **Rendering Layer** (`core/rendering/`)
- Generates PNG images for each mode
- Handles layout calculations
- Applies themes and colors
- Manages text rendering and positioning
- Leverages PIL/Pillow for image creation

**Files:**
- `sports_display_png.py` - Scoreboard layouts
- `weather_display_png.py` - Weather display
- `stocks_display_png.py` - Stock ticker
- `clock_display_png.py` - Clock themes

### 3. **Data Layer** (`core/data/`)
- Fetches real-time data from APIs
- Caches results to minimize API calls
- Error handling for API failures
- Provides clean data to renderers

**Files:**
- `sports_data.py` - ESPN API integration
- `weather_data.py` - OpenWeatherMap API
- `stocks_data.py` - Yahoo Finance API

### 4. **Configuration Layer** (`config_loader.py`)
- YAML configuration management
- Type helpers (get_bool, get_int, get_list)
- Dot-notation access to settings
- Fallback to environment variables

### 5. **Panel Management Layer** (`panel_core.py`)
- Manages adapter lifecycle
- Handles connection/disconnection
- Routes display commands to hardware
- Manages multiple panels

### 6. **Adapter Layer** (`adapters/`)
- Plugin architecture for hardware support
- Abstract base class defines interface
- Registry system for dynamic loading
- Specific implementations per hardware type

**Key Files:**
- `base.py` - DisplayAdapter interface
- `loader.py` - Dynamic adapter loading
- `adapters.json` - Adapter registry
- `ipixel/` - iPixel BLE adapter

### 7. **Protocol Layer** (`adapters/ipixel/protocol.py`)
- Low-level BLE communication
- PNG packet creation and transmission
- GIF animation support
- Multi-panel coordination
- Error recovery and retries

## Data Flow

### Display Update Flow
```
display_manager.py
    ↓
   Get Mode (sports/clock/weather/stocks)
    ↓
   Fetch Data (if needed)
    ↓
   Render PNG Image
    ↓
   Upload to Panels (via adapter)
    ↓
   Wait & Refresh
```

### Adapter Architecture Flow
```
Panel Manager
    ↓
Get Adapter (from registry)
    ↓
Create/Connect Adapter
    ↓
Upload Image (protocol-specific)
    ↓
Hardware Receives Data
```

## Key Design Patterns

### 1. **Plugin Architecture**
- New hardware support by creating new adapters
- No changes to core application
- Adapters registered in `adapters.json`

### 2. **Async/Await**
- Non-blocking BLE communication
- Responsive UI even during slow operations
- Proper error handling with timeouts

### 3. **Configuration as Code**
- YAML configuration stored separately
- Type helpers for clean access
- Support for environment variable overrides

### 4. **Layered Rendering**
- Separation of concerns (data, rendering, display)
- Easy to add new display modes
- Reusable rendering components

### 5. **Mode Switching**
- Priority-based (sports > others)
- Time-based cycling
- Seamless transitions

## Extension Points

### Adding New Display Mode
1. Create renderer in `core/rendering/`
2. Add data fetcher in `core/data/`
3. Register in `display_manager.py`
4. Add configuration in `config.yml`

### Adding New Hardware
1. Create adapter in `adapters/new_hardware/`
2. Implement `DisplayAdapter` interface
3. Register in `adapters.json`
4. Add configuration section in `config.yml.example`

### Customizing Display
1. Update YAML configuration
2. Themes, colors, modes all configurable
3. No code changes needed

## Dependencies

```
External Libraries:
├── bleak          # BLE communication
├── pillow         # Image processing
├── pyyaml         # Configuration
├── httpx          # HTTP requests
└── yfinance       # Stock data

Internal Modules:
├── core/          # Rendering & data logic
├── adapters/      # Hardware interfaces
├── config_loader/ # Configuration management
└── panel_core/    # Display coordination
```

## Performance Considerations

- **BLE Bandwidth** - PNG is efficient for small panels
- **Rendering** - PIL is fast for simple layouts
- **API Calls** - Cached and rate-limited
- **Update Interval** - Configurable per mode
- **Multi-Panel** - Parallel transmission when possible

## Thread Safety

- **Async Model** - Uses asyncio for concurrency
- **Single Writer** - One adapter connection per panel
- **No Shared State** - Data flows unidirectionally
- **Lock-Free** - Event-based synchronization

## Error Handling

- **Connection Failures** - Automatic reconnect
- **API Failures** - Graceful degradation
- **Rendering Errors** - Fallback displays
- **Configuration Errors** - Clear error messages

