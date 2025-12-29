# Dynamic Colors in Templates

## Overview

Templates support **dynamic color resolution** - special color names that change based on data.

## Sports Mode Colors

### Team Colors (Auto-Detected)

Use these color names for automatic team color matching:

```yaml
sports:
  one_item:
    away_score:
      color: "away_team"  # Uses away team's primary color
    
    away_name:
      color: "away_team"  # Same team color
    
    home_score:
      color: "home_team"  # Uses home team's primary color
    
    home_name:
      color: "home_team"  # Same team color
```

**How it works:**
- System looks up team (e.g., "BOS", "DET")
- Gets team color from `TEAM_COLORS` dictionary
- BOS → (0, 122, 51) Green
- DET → (200, 16, 46) Red
- Renders text in that color!

### Game Status Colors

```yaml
period:
  color: "time"  # Yellow (255, 255, 0) for time indicators

clock:
  color: "time"  # Yellow (255, 255, 0) for clocks
```

### Static Colors

You can also use static colors:

```yaml
color: "white"   # (255, 255, 255)
color: "gray"    # (128, 128, 128)
color: "red"     # (255, 0, 0)
color: "green"   # (0, 255, 0)
color: "blue"    # (0, 0, 255)
color: "yellow"  # (255, 255, 0)
color: "cyan"    # (0, 255, 255)
```

Or hex codes:
```yaml
color: "#667eea"  # Custom purple
color: "#ff4444"  # Custom red
```

## Stocks Mode Colors

### Change-Based Colors (Auto Green/Red)

```yaml
stocks:
  one_item:
    symbol:
      color: "white"  # Static white
    
    price:
      color: "change_color"  # Green if up, red if down!
    
    change:
      color: "change_color"  # Green if up, red if down!
    
    change_percent:
      color: "change_color"  # Green if up, red if down!
```

**How it works:**
- System checks `is_up` field in stock data
- If `is_up: True` → Green (0, 255, 0)
- If `is_up: False` → Red (255, 0, 0)
- Automatically matches stock performance!

## Weather Mode Colors

### Temperature-Based Colors (Auto)

```yaml
weather:
  one_item:
    temperature:
      color: "temp_color"  # Auto: Blue (cold) / Orange (cool) / Yellow (warm)
```

**How it works:**
- ≤ 45°F → Blue (0, 100, 255)
- 46-60°F → Orange (255, 140, 0)
- 61°F+ → Yellow (255, 255, 0)

### Static Weather Colors

```yaml
condition:
  color: "cyan"  # Light blue for conditions

humidity:
  color: "blue"  # Blue for humidity

feels_like:
  color: "gray"  # Gray for feels-like temp
```

## Available Dynamic Colors

| Color Name | Usage | Resolves To |
|------------|-------|-------------|
| `away_team` | Sports | Away team's primary color |
| `home_team` | Sports | Home team's primary color |
| `time` | Sports | Yellow (255, 255, 0) |
| `change_color` | Stocks | Green (up) / Red (down) |
| `temp_color` | Weather | Blue/Orange/Yellow (by temp) |

## Available Static Colors

| Color Name | RGB |
|------------|-----|
| `white` | (255, 255, 255) |
| `gray` | (128, 128, 128) |
| `red` | (255, 0, 0) |
| `green` | (0, 255, 0) |
| `blue` | (0, 0, 255) |
| `yellow` | (255, 255, 0) |
| `cyan` | (0, 255, 255) |
| `magenta` | (255, 0, 255) |

## Examples

### Sports - Full Team Colors

```yaml
sports:
  one_item:
    away_logo: { x: 2, y: 2, width: 16, height: 16 }
    away_score: { x: 22, y: 2, font_size: 14, color: "away_team" }
    away_name: { x: 22, y: 16, font_size: 8, color: "away_team" }
    
    home_logo: { x: 2, y: 22, width: 16, height: 16 }
    home_score: { x: 22, y: 22, font_size: 14, color: "home_team" }
    home_name: { x: 22, y: 36, font_size: 8, color: "home_team" }
    
    period: { x: 58, y: 2, font_size: 8, color: "time" }
    clock: { x: 58, y: 22, font_size: 8, color: "time" }
```

Result:
- BOS score appears in Celtics green
- DET score appears in Pistons red
- Period/clock in yellow

### Stocks - Dynamic Change Colors

```yaml
stocks:
  one_item:
    symbol: { x: 2, y: 2, font_size: 10, color: "white" }
    price: { x: 2, y: 12, font_size: 10, color: "change_color" }
    change_percent: { x: 2, y: 22, font_size: 9, color: "change_color" }
```

Result:
- AAPL up 2.3% → Green price and percentage
- TSLA down 1.2% → Red price and percentage

### Weather - Temperature Colors

```yaml
weather:
  one_item:
    temperature: { x: 22, y: 2, font_size: 12, color: "temp_color" }
    feels_like: { x: 22, y: 16, font_size: 8, color: "gray" }
    condition: { x: 2, y: 24, font_size: 8, color: "cyan" }
```

Result:
- 45°F → Blue
- 55°F → Orange
- 75°F → Yellow

## Best Practices

✅ **Use dynamic colors** for data-driven content  
✅ **Use static colors** for labels and decorations  
✅ **Consistent scheme** across all scenarios  
✅ **Team colors** make scores more readable  
✅ **Change colors** show stock performance at a glance  

## Color Resolution

The renderer resolves colors in this order:
1. Check for dynamic color name (away_team, change_color, etc.)
2. Check for static color name (white, red, etc.)
3. Parse as hex code (#667eea)
4. Fall back to white (255, 255, 255)

---

**Use dynamic colors for beautiful, data-driven displays!** 🎨

