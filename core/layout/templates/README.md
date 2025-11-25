# Layout Templates

This directory contains layout template files that define how content is displayed on LED panels.

## How It Works

1. **Automatic Selection**: The system automatically selects a matching template based on your display dimensions
2. **Manual Override**: Define your own template in `config.yml` under `layout_templates`
3. **Custom Templates**: Save your own template files here for reuse

## File Naming Convention

### Unified Templates (Recommended)

Templates are named: `{width}x{height}.yml`

Each file contains **all modes** (sports, stocks, weather):

```yaml
# 64x32.yml
sports:
  canvas_width: 64
  # ... sports layout
stocks:
  canvas_width: 64
  # ... stocks layout
weather:
  canvas_width: 64
  # ... weather layout
```

Examples:
- `32x32.yml` - All modes for 32×32 displays
- `64x32.yml` - All modes for 64×32 displays
- `128x20.yml` - All modes for dual iPixel panels

### Legacy Format (Still Supported)

Mode-specific files: `{width}x{height}_{mode}.yml`

Examples:
- `32x32_sports.yml` - Only sports
- `my_custom_sports.yml` - Your custom sports only

**Note:** Unified format is preferred for easier management!

## Using Templates

### Automatic (Recommended)

The system will automatically use the best matching template for your display size:

```yaml
# config.yml
display:
  ipixel:
    size_width: 64
    size_height: 32
```

System automatically loads `64x32_sports.yml` for sports mode!

### Manual Selection

Specify a template by name in `config.yml`:

```yaml
layout_templates:
  sports:
    template_file: "my_custom_sports.yml"
```

### Inline Definition

Define layout directly in `config.yml` (overrides template files):

```yaml
layout_templates:
  sports:
    canvas_width: 64
    canvas_height: 32
    logo_enabled: true
    one_item:
      away_logo:
        x: 2
        y: 2
        # ... etc
```

## Creating Custom Templates

### Method 1: Layout Builder (Easiest)

1. Open `http://localhost:8080/builder`
2. Load a preset or start fresh
3. Customize your layout
4. Click "⬇️ Download YAML"
5. Save to this directory as `my_layout.yml`

### Method 2: Copy and Modify

```bash
# Copy an existing template
cp 64x32_sports.yml my_custom_sports.yml

# Edit it
vim my_custom_sports.yml

# Use it
# Just restart - auto-detected by filename!
```

### Method 3: From Scratch

Create a new `.yml` file with this structure:

```yaml
canvas_width: 64
canvas_height: 32
logo_enabled: true

one_item:
  # Single game layout
  away_logo:
    x: 2
    y: 2
    width: 12
    height: 12
  away_score:
    x: 18
    y: 4
    font_size: 12
    color: "away_team"
  # ... more elements

two_items:
  # Two games layout
  item_height: 16
  item_template:
    # Elements for each game
    away_text:
      x: 1
      y: 1
      font_size: 8
      # ... etc
```

## Available Templates

### Standard Sizes

- `16x16_sports.yml` - Tiny square (text only)
- `16x32_sports.yml` - Portrait (vertical)
- `32x32_sports.yml` - Square (small logos)
- `64x32_sports.yml` - Wide (standard)
- `64x64_sports.yml` - Large square (detailed)

### Custom Templates

Your custom templates appear here when you save them from the Layout Builder!

## Template Priority

Templates are loaded in this order:

1. **Inline in config.yml** (highest priority)
2. **Specified template_file** in config
3. **Auto-detected by dimensions** (e.g., `64x32_sports.yml`)
4. **Fallback to code defaults** (lowest priority)

## Sharing Templates

Templates are just YAML files - easy to share!

```bash
# Share your template
cp my_awesome_layout.yml ~/Desktop/
# Send to friend

# Use someone else's template
cp ~/Downloads/cool_layout.yml core/layout/templates/
# Restart - auto-detected!
```

## Tips

- **Name descriptively**: `my_dual_panel_sports.yml` better than `layout1.yml`
- **Add comments**: Document why you chose specific values
- **Version control**: Commit good templates to git
- **Test in emulator**: Use `python3 emulator.py` to test before hardware
- **Start from presets**: Easier than starting from scratch

## Element Properties

### Logo Elements
- `x`, `y`: Position in pixels
- `width`, `height`: Logo dimensions

### Text Elements
- `x`, `y`: Position in pixels
- `font_size`: Text size in points
- `color`: Color name (e.g., "away_team", "home_team", "#FF0000")
- `align`: "left", "center", or "right"
- `format`: Template string (e.g., "{abbr} {score}")

### Color Names
- `away_team` - Resolves to away team's color
- `home_team` - Resolves to home team's color
- `time` - Yellow (for clocks/periods)
- `change_color` - Green (up) or Red (down) for stocks
- `#RRGGBB` - Any hex color

## Need Help?

- See [layout-presets.md](../../../docs/layout-presets.md) for examples
- Use [Layout Builder](../../../docs/layout-builder.md) for visual design
- Check [standard-sizes.md](../../../docs/standard-sizes.md) for guidance

