# Clock Themes Guide

Create custom themed clocks with PNG rendering! Easily switch between themes and create your own.

## Configuring Theme

In `config.env`:
```bash
CLOCK_THEME=stranger_things  # Change this to any theme name
CLOCK_24H=false              # false = 12-hour, true = 24-hour
```

## Built-in Themes

### stranger_things
**Style:** Inspired by the Stranger Things logo  
**Colors:** Red text with dark red glow  
**Effect:** Glow effect around text for retro aesthetic

```python
"stranger_things": {
    "bg_color": (0, 0, 0),           # Black background
    "time_color": (255, 50, 50),     # Red time
    "date_color": (150, 150, 150),   # Gray date
    "time_size": 16,
    "date_size": 8,
    "glow": True,                    # Enable glow
    "glow_color": (50, 0, 0),        # Dark red glow
}
```

---

### classic
**Style:** Classic digital clock  
**Colors:** Cyan time, yellow date  
**Effect:** Clean and simple

```python
"classic": {
    "bg_color": (0, 0, 0),           # Black background
    "time_color": (0, 255, 255),     # Cyan time
    "date_color": (255, 255, 0),     # Yellow date
    "time_size": 16,
    "date_size": 8,
    "glow": False,
}
```

---

### matrix
**Style:** Matrix/hacker aesthetic  
**Colors:** Green on black  
**Effect:** Minimal, tech-inspired

```python
"matrix": {
    "bg_color": (0, 0, 0),           # Black background
    "time_color": (0, 255, 0),       # Bright green time
    "date_color": (0, 180, 0),       # Darker green date
    "time_size": 16,
    "date_size": 8,
    "glow": False,
}
```

---

## Creating Custom Themes

**No code changes needed!** Create themes using a JSON file.

### Step 1: Create Custom Themes File

Copy the example:
```bash
cp custom_themes.json.example custom_themes.json
```

### Step 2: Define Your Theme

Edit `custom_themes.json` and add your theme:

```json
{
  "your_theme_name": {
    "bg_color": [0, 0, 0],
    "time_color": [255, 0, 0],
    "date_color": [150, 150, 150],
    "font_time": "./fonts/PixelOperator.ttf",
    "font_date": "./fonts/PixelOperator.ttf",
    "time_size": 16,
    "date_size": 8,
    "glow": false,
    "glow_color": [50, 0, 0]
  }
}
```

**Note:** Use arrays `[R, G, B]` for colors (not tuples) and lowercase `true`/`false` for booleans (JSON format).

### Step 3: Configure

Update `config.env`:
```bash
CLOCK_THEME=your_theme_name
```

### Step 4: Test

```bash
python display_manager.py
```

You should see: `✅ Loaded 1 custom clock theme(s) from custom_themes.json`

Your custom theme should appear!

### Multiple Custom Themes

You can define multiple themes in one file:

```json
{
  "theme_one": { ... },
  "theme_two": { ... },
  "theme_three": { ... }
}
```

Then switch between them by changing `CLOCK_THEME` in config.env.

---

## Theme Design Guide

### Color Selection

**RGB values:** (Red, Green, Blue) from 0-255

**Good color combinations:**
- Red on black: `(255, 0, 0)` on `(0, 0, 0)`
- Cyan on black: `(0, 255, 255)` on `(0, 0, 0)`
- Green on black: `(0, 255, 0)` on `(0, 0, 0)`
- Yellow on black: `(255, 255, 0)` on `(0, 0, 0)`
- White on black: `(255, 255, 255)` on `(0, 0, 0)`

**Avoid:**
- Low contrast (hard to read on small display)
- Bright backgrounds (wastes battery, hurts eyes in dark)

### Font Sizing

**Display constraints:**
- Top panel: 64x20 pixels
- Bottom panel: 64x20 pixels (shows weather)
- Time must fit in top panel

**Recommended sizes:**
- `time_size`: 14-18 pixels (16 is ideal)
- `date_size`: 6-10 pixels (8 is ideal)

**Testing different sizes:**
```python
# Larger time (may need to adjust layout)
"time_size": 18,
"date_size": 8,

# Smaller time (more space for date)
"time_size": 14,
"date_size": 10,
```

### Glow Effect

The glow effect adds a subtle halo around text.

**Enable glow:**
```python
"glow": True,
"glow_color": (50, 0, 0),  # Dark version of time_color
```

**Glow tips:**
- Use darker version of your time_color
- Example: time is `(255, 0, 0)` → glow is `(50, 0, 0)`
- Subtle glows work best (50-100 range)
- Too bright = text becomes unreadable

**Glow examples:**
```python
# Red glow
"time_color": (255, 50, 50),
"glow_color": (50, 0, 0),

# Blue glow
"time_color": (100, 150, 255),
"glow_color": (0, 0, 50),

# Green glow
"time_color": (0, 255, 0),
"glow_color": (0, 50, 0),
```

---

## Using Custom Fonts

### Step 1: Add Font File

Place your font file in the `fonts/` directory:
```bash
fonts/
├── PixelOperator.ttf (default)
├── Rain-DRM3.otf
└── YourCustomFont.ttf (add yours)
```

### Step 2: Reference in Theme

```python
"your_theme": {
    "font_time": "./fonts/YourCustomFont.ttf",
    "font_date": "./fonts/YourCustomFont.ttf",
    # ... other settings ...
}
```

### Step 3: Adjust Sizing

Different fonts render at different sizes. Test and adjust:
```python
"time_size": 14,  # May need to adjust
"date_size": 7,   # May need to adjust
```

### Font Recommendations

**Pixel/Bitmap fonts** work best on small displays:
- PixelOperator (included)
- BitFont
- Press Start 2P
- Pixel Millennium
- VCR OSD Mono

**Avoid:**
- Serif fonts (too detailed)
- Script fonts (unreadable at small sizes)
- Very thin fonts (hard to see)

---

## Example Custom Themes

Copy any of these into your `custom_themes.json`:

### Neon Blue
```json
"neon_blue": {
  "bg_color": [0, 0, 0],
  "time_color": [0, 200, 255],
  "date_color": [0, 150, 200],
  "font_time": "./fonts/PixelOperator.ttf",
  "font_date": "./fonts/PixelOperator.ttf",
  "time_size": 16,
  "date_size": 8,
  "glow": true,
  "glow_color": [0, 0, 100]
}
```

### Fire
```json
"fire": {
  "bg_color": [0, 0, 0],
  "time_color": [255, 100, 0],
  "date_color": [200, 50, 0],
  "font_time": "./fonts/PixelOperator.ttf",
  "font_date": "./fonts/PixelOperator.ttf",
  "time_size": 16,
  "date_size": 8,
  "glow": true,
  "glow_color": [100, 0, 0]
}
```

### Minimal White
```json
"minimal": {
  "bg_color": [0, 0, 0],
  "time_color": [255, 255, 255],
  "date_color": [180, 180, 180],
  "font_time": "./fonts/PixelOperator.ttf",
  "font_date": "./fonts/PixelOperator.ttf",
  "time_size": 16,
  "date_size": 8,
  "glow": false
}
```

### Synthwave
```json
"synthwave": {
  "bg_color": [0, 0, 0],
  "time_color": [255, 0, 255],
  "date_color": [255, 100, 200],
  "font_time": "./fonts/PixelOperator.ttf",
  "font_date": "./fonts/PixelOperator.ttf",
  "time_size": 16,
  "date_size": 8,
  "glow": true,
  "glow_color": [50, 0, 50]
}
```

### Terminal Green
```json
"terminal": {
  "bg_color": [0, 0, 0],
  "time_color": [0, 255, 100],
  "date_color": [0, 200, 80],
  "font_time": "./fonts/PixelOperator.ttf",
  "font_date": "./fonts/PixelOperator.ttf",
  "time_size": 16,
  "date_size": 8,
  "glow": false
}
```

**Using multiple themes:**
```json
{
  "neon_blue": { ... },
  "fire": { ... },
  "minimal": { ... }
}
```

---

## Tips & Best Practices

### Readability First
- High contrast is critical on small displays
- Test in different lighting conditions
- Prefer bold/thick fonts over thin ones

### Color Harmony
- Date color should complement time color
- Use lighter/darker variants of same hue
- Or use complementary colors (e.g., cyan time + yellow date)

### Testing
```bash
# Quick test without restarting
CLOCK_THEME=your_theme python display_manager.py
```

### Sharing Themes
If you create cool themes, share them!
1. Add your theme to `custom_themes.json.example`
2. Document in this file with description
3. Submit a pull request

Your theme will be available for others to use!

---

## Troubleshooting

### "Theme not found"
**Problem:** Typo in theme name

**Solution:** Check spelling in config.env matches THEMES dict exactly

### "Time doesn't fit"
**Problem:** Font size too large

**Solution:** Reduce `time_size` in theme:
```python
"time_size": 14,  # Reduce from 16
```

### "Font file not found"
**Problem:** Font path incorrect

**Solution:** Verify font exists:
```bash
ls fonts/YourFont.ttf
```

Use relative path from project root:
```python
"font_time": "./fonts/YourFont.ttf",
```

### "Glow too bright / text unreadable"
**Problem:** Glow color too bright

**Solution:** Use darker glow values:
```python
"glow_color": (30, 0, 0),  # Very subtle
```

---

## Advanced: Dynamic Themes

Want themes that change based on time of day?

1. Define all your time-based themes in `custom_themes.json`:
   ```json
   {
     "morning_bright": { "time_color": [255, 200, 0], ... },
     "afternoon_warm": { "time_color": [255, 150, 50], ... },
     "evening_cool": { "time_color": [100, 150, 255], ... },
     "night_dim": { "time_color": [100, 100, 150], ... }
   }
   ```

2. Modify `clock_display_png.py` to add time-based logic:
   ```python
   def get_dynamic_theme():
       hour = datetime.now().hour
       if 6 <= hour < 12:
           return "morning_bright"
       elif 12 <= hour < 18:
           return "afternoon_warm"
       elif 18 <= hour < 22:
           return "evening_cool"
       else:
           return "night_dim"
   
   # In render_clock():
   theme_name = get_dynamic_theme() if CLOCK_THEME == "dynamic" else CLOCK_THEME
   ```

3. Set `CLOCK_THEME=dynamic` in config.env

**Note:** This requires code modification, but your themes stay in JSON!

---

## Need Help?

- **Configuration:** See [Configuration Guide](configuration.md)
- **Setup:** See [Setup Guide](setup.md)
- **Issues:** Open a GitHub issue
- **Share themes:** Submit a pull request!

---

**Next:** [Configuration Guide](configuration.md) | [Setup Guide](setup.md)

