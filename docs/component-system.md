# Component-Based Rendering System

## Overview

The component system allows you to create **composite templates** by combining independent, reusable widgets. Instead of being locked into predefined "modes," you can drag-and-drop components to create any layout you want.

## Philosophy

### Old Way (Mode-Based)
```yaml
# Separate modes that can't be mixed
sports: { ... }
weather: { ... }
clock: { ... }
```
- ❌ Can't combine clock + weather
- ❌ Each mode is a separate template
- ❌ Hard to create custom layouts

### New Way (Component-Based)
```yaml
# Mix and match components
components:
  - type: clock
    x: 0, y: 0
  - type: weather_extended
    x: 0, y: 20
```
- ✅ Combine any components
- ✅ Position anywhere
- ✅ Infinite flexibility

## Available Components

### `clock`
Displays current time with themes.

**Config:**
- `theme`: Clock theme ("stranger_things", "retro", "matrix")
- `hour24`: Use 24-hour format (default: false)

**Example:**
```yaml
- type: clock
  x: 0
  y: 0
  width: 64
  height: 20
  config:
    theme: "stranger_things"
    hour24: false
```

### `weather_current`
Shows current weather with icon, temp, condition.

**Config:**
- `zipcode`: Override default zipcode
- `show_icon`: Show weather icon (default: true)
- `show_feels_like`: Show feels-like temp (default: false)

**Example:**
```yaml
- type: weather_current
  x: 0
  y: 0
  width: 64
  height: 20
  config:
    show_icon: true
```

### `weather_extended`
Multi-day forecast with icons and high/low temps.

**Config:**
- `days`: Number of days to show (default: 4)
- `zipcode`: Override default zipcode

**Example:**
```yaml
- type: weather_extended
  x: 0
  y: 20
  width: 64
  height: 20
  config:
    days: 4
```

### `sports_live`
Live or upcoming sports games.

**Config:**
- `leagues`: List of leagues (default: all)
- `states`: Game states ["LIVE", "UPCOMING", "COMPLETED"]
- `max_games`: Max games to show
- `filter_teams`: Only show games with these teams

**Example:**
```yaml
- type: sports_live
  x: 0
  y: 0
  width: 64
  height: 20
  config:
    leagues: ["NBA", "NFL"]
    states: ["LIVE", "UPCOMING"]
    max_games: 2
```

### `stocks`
Stock quotes with prices and changes.

**Config:**
- `symbols`: List of stock symbols
- `screener`: Use screener ("GAINERS", "LOSERS", "MOST_ACTIVE")
- `limit`: Max stocks to show

**Example:**
```yaml
- type: stocks
  x: 0
  y: 0
  width: 64
  height: 20
  config:
    screener: "GAINERS"
    limit: 3
```

## Creating a Composite Template

### Template Structure

```yaml
name: "my_template"           # Template name
canvas_width: 64              # Total canvas width
canvas_height: 40             # Total canvas height
background_color: [0, 0, 0]   # RGB background

components:
  - type: "component_type"    # Component type
    x: 0                      # X position
    y: 0                      # Y position
    width: 64                 # Component width
    height: 20                # Component height
    config:                   # Component-specific config
      option1: value1
      option2: value2
```

### Example: Clock + Weather

```yaml
name: "clock_with_weather"
canvas_width: 64
canvas_height: 40
background_color: [0, 0, 0]

components:
  # Clock on top
  - type: "clock"
    x: 0
    y: 0
    width: 64
    height: 20
    config:
      theme: "stranger_things"
  
  # Weather forecast on bottom
  - type: "weather_extended"
    x: 0
    y: 20
    width: 64
    height: 20
    config:
      days: 4
```

### Example: Information Dashboard

```yaml
name: "dashboard"
canvas_width: 128
canvas_height: 40

components:
  # Top-left: Clock
  - type: "clock"
    x: 0
    y: 0
    width: 64
    height: 20
  
  # Top-right: Weather
  - type: "weather_current"
    x: 64
    y: 0
    width: 64
    height: 20
  
  # Bottom-left: Sports
  - type: "sports_live"
    x: 0
    y: 20
    width: 64
    height: 20
  
  # Bottom-right: Stocks
  - type: "stocks"
    x: 64
    y: 20
    width: 64
    height: 20
```

## Using Composite Templates

### In Python

```python
from core.components import registry
from core.components.composite_renderer import load_composite_template

# Load template
renderer = load_composite_template('templates/clock_with_weather.yml', registry)

# Render (fetches data and renders all components)
image = await renderer.render()

# Display
await display.upload_image(image)
```

### Creating a Custom Component

```python
from core.components.base import Component
from PIL import Image

class MyCustomComponent(Component):
    """My custom widget."""
    
    async def fetch_data(self):
        """Fetch any data needed."""
        return {"my": "data"}
    
    def render(self, data):
        """Render the component."""
        img = Image.new('RGB', (self.width, self.height), (0, 0, 0))
        # ... draw on img ...
        return img

# Register it
from core.components import registry
registry.register('my_component', MyCustomComponent)
```

## Template Builder (Future)

The component system is designed to support a visual template builder:

1. **Drag & Drop**: Drag components onto a canvas
2. **Position**: Move and resize components
3. **Configure**: Edit component options in a panel
4. **Preview**: See real-time preview with live data
5. **Export**: Save as YAML template

### UI Mockup
```
┌─────────────────────────────────────────────┐
│ Component Palette                           │
├─────────────────────────────────────────────┤
│ [Clock] [Weather] [Sports] [Stocks]         │
└─────────────────────────────────────────────┘

┌─────────────────────┐  ┌──────────────────┐
│ Canvas (64x40)      │  │ Properties       │
│                     │  │                  │
│  ┌──────────────┐   │  │ Component: Clock │
│  │   Clock      │   │  │ x: 0             │
│  │   12:34 PM   │   │  │ y: 0             │
│  └──────────────┘   │  │ width: 64        │
│  ┌──────────────┐   │  │ height: 20       │
│  │Mon Tue Wed   │   │  │                  │
│  │☀️  ☁️  🌧️   │   │  │ theme: retro     │
│  │75° 68° 62°   │   │  │ hour24: false    │
│  └──────────────┘   │  └──────────────────┘
└─────────────────────┘
```

## Benefits

1. **Flexibility**: Create any layout
2. **Reusability**: Components work anywhere
3. **Maintainability**: Each component is independent
4. **Testability**: Test components in isolation
5. **Builder-Friendly**: Easy to generate from UI

## Migration Path

### Phase 1: Component Foundation (Current)
- ✅ Component base classes
- ✅ Core components (clock, weather, sports, stocks)
- ✅ Composite renderer
- ✅ Example templates

### Phase 2: Display Integration
- Create CompositeMode that uses composite templates
- Add template selection to config
- Support template hot-reloading

### Phase 3: Template Builder
- Web-based template builder UI
- Drag-and-drop interface
- Live preview with real data
- Template library

## Files

- `core/components/base.py` - Base classes
- `core/components/*.py` - Component implementations
- `core/components/composite_renderer.py` - Composite renderer
- `templates/*.yml` - Example composite templates

---

**Ready to build your own layouts!** 🎨


