# Layout Templates Guide

## Overview

Layout templates allow you to customize exactly how content is positioned on your LED panels. Instead of hardcoded layouts optimized for dual 20×64 panels, you can define custom element positioning for ANY panel configuration.

## Why Use Layout Templates?

The original codebase was optimized for **two 20×64 panels** (total 64×40 pixels). If you have:
- **Single 64×64 panel**: More space for larger logos and fonts
- **Single 32×16 panel**: Need compact, efficient layouts
- **Three or more panels**: Can display more items simultaneously
- **Custom arrangements**: Vertical stacking, side-by-side, etc.

Layout templates give you **pixel-perfect control** over every element.

## How It Works

### 1. Default Behavior (No Custom Templates)

Without defining custom templates, the system automatically uses smart defaults that replicate the original hardcoded behavior for dual 20×64 panels.

### 2. Custom Templates (Optional)

Add a `layout_templates` section to your `config.yml` to override defaults:

```yaml
layout_templates:
  sports:
    # Define layouts for 1 game, 2 games, etc.
  stocks:
    # Define layouts for 1 stock, 2 stocks, etc.
```

## Sports Templates

### Structure

```yaml
layout_templates:
  sports:
    logo_enabled: true  # Show team logos?
    
    one_game:
      # Layout when displaying 1 game (full screen)
    
    two_games:
      # Layout when displaying 2 games
    
    three_games:
      # Layout when displaying 3 games
    
    four_games:
      # Layout when displaying 4 games
```

### Element Types

Each game layout can include these elements:

#### Single Game Elements (one_game)
- `away_logo`: Away team logo position and size
- `away_name`: Away team name text
- `away_score`: Away team score
- `home_logo`: Home team logo position and size
- `home_name`: Home team name text
- `home_score`: Home team score
- `period`: Game period (Q1, Q2, etc.)
- `clock`: Game clock (time remaining)
- `time`: Game start time (for upcoming games)

#### Multi-Game Elements (two_games, three_games, four_games)
For multiple games, you typically use **repeating templates**:
- `game_height`: Vertical space per game (pixels)
- `game_template`: Template that repeats for each game
  - `away_text`: Combined away team info (e.g., "DET 5")
  - `home_text`: Combined home team info
  - `period`, `clock`: Same as single game

### Element Properties

Each element can have:

```yaml
element_name:
  x: 10              # X position (pixels from left)
  y: 5               # Y position (pixels from top)
  width: 16          # Width (for logos)
  height: 16         # Height (for logos)
  font_size: 12      # Font size (pixels)
  color: "white"     # Color (see Color Options below)
  align: "left"      # Text alignment: left, right, center
  format: "{abbr} {score}"  # Text format string
```

### Color Options

**Named colors:**
- `"white"`, `"black"`, `"red"`, `"green"`, `"blue"`, `"yellow"`, `"orange"`, `"cyan"`, `"magenta"`

**Dynamic colors:**
- `"away_team"` - Uses away team's official color
- `"home_team"` - Uses home team's official color
- `"time"` - Yellow (for clock/period)

**RGB tuples:**
- `[255, 0, 0]` - Custom RGB color

### Format Strings

For text elements with `format` property:
- `{abbr}` - Team abbreviation (e.g., "DET")
- `{name}` - Full team name
- `{score}` - Team score

Example: `"{abbr} {score}"` → "DET 5"

## Stocks Templates

### Structure

```yaml
layout_templates:
  stocks:
    one_stock:
      # Layout when displaying 1 stock
    
    two_stocks:
      # Layout when displaying 2 stocks
    
    four_stocks:
      # Layout when displaying 4 stocks
```

### Element Types

- `symbol`: Stock ticker symbol (e.g., "AAPL")
- `name`: Company name
- `price`: Current price
- `change`: Price change amount
- `change_percent`: Percentage change

### Dynamic Colors

- `"change_color"` - Automatically green (up) or red (down)

## Complete Examples

### Example 1: Single 64×64 Panel (Sports)

```yaml
layout_templates:
  sports:
    logo_enabled: true
    
    one_game:
      # Larger logos and text for big panel
      away_logo: { x: 4, y: 4, width: 24, height: 24 }
      away_name: { x: 32, y: 8, font_size: 14, color: "away_team" }
      away_score: { x: 32, y: 24, font_size: 16, color: "away_team" }
      
      home_logo: { x: 4, y: 36, width: 24, height: 24 }
      home_name: { x: 32, y: 40, font_size: 14, color: "home_team" }
      home_score: { x: 32, y: 56, font_size: 16, color: "home_team" }
      
      period: { x: 4, y: 4, font_size: 10, color: "time", align: "right" }
      clock: { x: 4, y: 16, font_size: 10, color: "time", align: "right" }
    
    two_games:
      game_height: 32  # Each game gets 32 pixels (64/2)
      game_template:
        away_logo: { x: 2, y: 2, width: 12, height: 12 }
        away_text: { x: 16, y: 4, font_size: 12, color: "away_team", format: "{abbr} {score}" }
        home_logo: { x: 2, y: 16, width: 12, height: 12 }
        home_text: { x: 16, y: 18, font_size: 12, color: "home_team", format: "{abbr} {score}" }
        period: { x: 4, y: 4, font_size: 9, color: "time", align: "right" }
```

### Example 2: Small 32×16 Panel (Stocks)

```yaml
layout_templates:
  stocks:
    one_stock:
      # Compact layout for tiny panel
      symbol: { x: 1, y: 1, font_size: 8, color: "white" }
      price: { x: 1, y: 9, font_size: 8, color: "change_color" }
    
    two_stocks:
      stock_height: 8
      stock_template:
        symbol: { x: 1, y: 0, font_size: 6, color: "white" }
        price: { x: 12, y: 0, font_size: 6, color: "change_color" }
```

### Example 3: Three Vertical Panels (64×60 total)

```yaml
layout_templates:
  sports:
    logo_enabled: true
    
    # Show 3 games at once (20px each)
    three_games:
      game_height: 20
      game_template:
        away_text: { x: 2, y: 2, font_size: 10, color: "away_team", format: "{abbr} {score}" }
        home_text: { x: 2, y: 11, font_size: 10, color: "home_team", format: "{abbr} {score}" }
        period: { x: 4, y: 2, font_size: 8, align: "right", color: "time" }
```

## Alignment Guide

### Left Alignment (default)
```yaml
text: { x: 10, y: 5, align: "left" }
# Text starts at x=10
```

### Right Alignment
```yaml
text: { x: 4, y: 5, align: "right" }
# Text ends at (panel_width - 4)
# x is now offset from RIGHT edge
```

### Center Alignment
```yaml
text: { x: 0, y: 5, align: "center" }
# Text center is at (panel_width / 2)
# x is offset from center
```

## Tips & Best Practices

### 1. Start with Defaults
Don't add `layout_templates` until you need custom positioning. The defaults work great for most setups.

### 2. Test One Element at a Time
When customizing, adjust one element's position and test before moving to the next.

### 3. Use Alignment for Dynamic Positioning
Instead of hardcoding right-side positions, use `align: "right"` so layouts adapt if you change panel width.

### 4. Mind the Panel Boundaries
For dual panels:
- Panel 1: y = 0-19
- Panel 2: y = 20-39

Avoid positioning text right on y=20 (it may bleed across panels).

### 5. Font Size vs. Element Height
- For 10px height, use font_size ≤ 8
- For 20px height, use font_size ≤ 14
- Leave 2-3px padding

### 6. Logo Sizing
Common logo sizes:
- **Full screen:** 16×16 or 24×24
- **Half screen:** 12×12
- **Compact:** 8×8

## Troubleshooting

### Text is Cut Off
- Reduce `font_size`
- Check `x` and `y` positions aren't too close to edges
- For right-aligned text, increase `x` offset

### Logos Not Showing
- Set `logo_enabled: true` in template
- Check logo files exist in `logos/{league}/{TEAM}.png`
- Verify `width` and `height` fit within allocated space

### Elements Overlap
- Increase `game_height` or `stock_height`
- Adjust `y` positions to space elements apart
- Reduce `font_size`

### Wrong Colors
- Check spelling of color names
- Use quotes: `color: "red"` not `color: red`
- For dynamic colors, verify context (team names, stock data)

## Advanced: Per-Item Templates

Instead of repeating templates, you can define unique layouts for each position:

```yaml
two_games:
  game_height: 20
  games:  # List of templates, one per game
    - # Game 1 template
      away_text: { x: 2, y: 2, font_size: 12, color: "away_team", format: "{abbr} {score}" }
      home_text: { x: 2, y: 12, font_size: 12, color: "home_team", format: "{abbr} {score}" }
    - # Game 2 template (different layout!)
      away_text: { x: 4, y: 2, font_size: 10, color: "away_team", format: "{name}" }
      home_text: { x: 4, y: 12, font_size: 10, color: "home_team", format: "{name}" }
```

This gives complete flexibility but requires more configuration.

## Migration from Legacy Code

If you're upgrading from the original hardcoded layouts:

1. **No action needed** - Defaults match old behavior
2. **To customize** - Add `layout_templates` section
3. **Backward compatible** - Old code still works

Your existing `config.yml` continues working without changes!

## Summary

Layout templates provide **ultimate flexibility** for any panel configuration:

✅ **Optional** - Use defaults or customize  
✅ **Per-scenario** - Different layouts for 1, 2, 3, 4+ items  
✅ **Element-level control** - Position every logo, text, score  
✅ **Dynamic colors** - Team colors, change indicators  
✅ **Format strings** - Customize text display  
✅ **Backward compatible** - Existing setups work unchanged  

See `config.yml.example` for complete examples!

