# Template Library Overview

## Unified Template System

**7 template files** covering **all modes** for standard display sizes!

### Template Files (Unified)

Each file contains layouts for **Sports, Stocks, and Weather**:

```
16x16.yml     - Tiny square (all 3 modes)
16x32.yml     - Portrait (all 3 modes)
32x32.yml     - Square (all 3 modes)
64x20.yml     - iPixel standard (all 3 modes)
64x32.yml     - Wide (all 3 modes)
64x64.yml     - Large square (all 3 modes)
128x20.yml    - iPixel dual (all 3 modes)
```

### Coverage Matrix

| Size | File | Sports | Stocks | Weather |
|------|------|--------|--------|---------|
| 16×16 | `16x16.yml` | ✅ | ✅ | ✅ |
| 16×32 | `16x32.yml` | ✅ | ✅ | ✅ |
| 32×32 | `32x32.yml` | ✅ | ✅ | ✅ |
| 64×20 | `64x20.yml` | ✅ | ✅ | ✅ |
| 64×32 | `64x32.yml` | ✅ | ✅ | ✅ |
| 64×64 | `64x64.yml` | ✅ | ✅ | ✅ |
| 128×20 | `128x20.yml` | ✅ | ✅ | ✅ |

**Result:** One file per size = easier to manage!

## Auto-Detection Examples

### Your Display: 64×20 (iPixel standard)
```yaml
# config.yml
display:
  ipixel:
    size_width: 64
    size_height: 20
```

**Auto-loads:** `64x20.yml` (contains all 3 modes!)

### Your Display: 128×20 (iPixel dual)
```yaml
# config.yml
display:
  ipixel:
    size_width: 64
    size_height: 20
    ble_addresses:
      - "XX:XX:XX:XX:XX:XX"
      - "YY:YY:YY:YY:YY:YY"  # 2 panels
```

**Auto-loads:** `128x20.yml` (contains all 3 modes!)

### Your Display: 64×64 (large square)
```yaml
# config.yml
display:
  ipixel:
    size_width: 64
    size_height: 64
```

**Auto-loads:** `64x64.yml` (contains all 3 modes!)

### Benefits

✅ **One file per display size** - Easier to manage  
✅ **All modes in sync** - Consistent spacing across modes  
✅ **Easier sharing** - Share one file, get all modes  
✅ **Simpler structure** - 7 files instead of 19+

## Template Features by Mode

### Sports Templates Include

- **Logos** - Team logos (if enabled)
- **Scores** - Home and away scores
- **Team Names** - Abbreviations
- **Game Clock** - Time remaining
- **Period** - Quarter/period indicator
- **Multi-game layouts** - 1, 2, 3, 4+ games

### Stocks Templates Include

- **Symbol** - Stock ticker symbol
- **Price** - Current price
- **Change** - Price change with ▲/▼
- **Change %** - Percentage change
- **Color coding** - Green (up) / Red (down)
- **Multi-stock layouts** - 1, 2, 4+ stocks

### Weather Templates Include

- **Icon** - Weather condition icon
- **Temperature** - Current temp
- **Feels Like** - Apparent temperature
- **Condition** - Description (sunny, cloudy, etc.)
- **Location** - Zip code
- **Humidity** - Relative humidity (large displays)
- **Wind** - Wind speed (large displays)

## Quick Reference

### Testing Different Sizes

```bash
# Tiny
python3 emulator.py -w 16 -y 16 -p 1

# Standard iPixel
python3 emulator.py -w 64 -y 20 -p 1

# Square
python3 emulator.py -w 32 -y 32 -p 1

# Wide
python3 emulator.py -w 64 -y 32 -p 1

# Large
python3 emulator.py -w 64 -y 64 -p 1

# Dual iPixel
python3 emulator.py -w 64 -y 20 -p 2
```

Each will auto-load the matching template for each mode!

## Customizing Templates

### Method 1: Visual Editor
```bash
# 1. Open builder
http://localhost:8080/builder

# 2. Browse templates → Select any template
# 3. Modify visually
# 4. Save with new name
```

### Method 2: Direct Edit
```bash
# 1. Copy a template
cp core/layout/templates/64x32_sports.yml \
   core/layout/templates/my_custom.yml

# 2. Edit in your favorite editor
vim core/layout/templates/my_custom.yml

# 3. Use it!
# Auto-loaded if dimensions match
```

### Method 3: Inline Override
```yaml
# In config.yml
layout_templates:
  sports:
    # Override specific elements
    one_item:
      away_logo:
        x: 4  # Different position
        # Other values from file
```

## Missing a Size?

### Create New Template

```bash
# 1. Find closest match
cp core/layout/templates/64x32_sports.yml \
   core/layout/templates/80x40_sports.yml

# 2. Edit dimensions and positions
vim core/layout/templates/80x40_sports.yml

# 3. Test in emulator
python3 emulator.py -w 80 -y 40 -p 1

# 4. Iterate until perfect!

# 5. Share with community (PR welcome!)
```

### Request Standard Template

Open an issue requesting a new standard size. Common requests:
- 128×32 (dual 64×32)
- 96×64 (three panels)
- 256×64 (large installation)

## Template Development

### Guidelines

1. **Start with presets** - Don't reinvent the wheel
2. **Use Layout Builder** - Visual is faster
3. **Test thoroughly** - All modes, all scenarios
4. **Document** - Add comments explaining choices
5. **Share** - Help others with similar displays

### Element Spacing

**General rules:**
- 2px margin from edges
- 4-6px between elements
- Text needs 1-2px vertical clearance
- Logos need 2-4px padding

**Font sizing:**
- 16×16: 6-7pt max
- 32×32: 8-10pt
- 64×32: 10-12pt
- 64×64: 12-16pt

### Color Scheme

Use dynamic colors:
- `away_team` - Auto team color
- `home_team` - Auto team color
- `change_color` - Green/red for stocks
- `time` - Yellow for clocks
- `white`, `gray`, `cyan` - Static colors

## Contributing Templates

Share your templates with the community!

```bash
# 1. Create your template
# 2. Test thoroughly
# 3. Add to git
git add core/layout/templates/my_awesome.yml

# 4. Commit with description
git commit -m "Add 80×40 sports layout with large fonts"

# 5. Push and create PR
git push origin my-template-branch
```

---

**Full template support for all modes!** 🎉

Sports, Stocks, and Weather all have templates across all standard sizes.

