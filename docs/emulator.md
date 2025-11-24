## LED Panel Emulator

### Overview

The LED Panel Emulator is a web-based virtual display that lets you test and visualize your LED panel output without physical hardware. Perfect for development, testing layouts, and previewing animations.

### Features

✨ **Real-time Preview** - See exactly what will be displayed on your physical panels  
🔄 **Hot Reload** - Automatic updates when config or templates change  
🎨 **Pixel-Perfect** - Renders at the exact resolution of your panels  
🖥️ **Multi-Panel Support** - Visualizes all panels in your configuration  
📊 **Live Stats** - Monitor frame count, data transfer, and update times  
🌐 **Web-Based** - No additional software needed, just open in your browser

### Installation

Install the required dependency:

```bash
pip install aiohttp>=3.8.0
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

### Quick Start

1. **Start the emulator:**

```bash
python emulator.py
```

2. **Open your browser:**

Navigate to `http://localhost:8080` (the URL will be shown in the terminal)

3. **See your display come to life!**

The emulator will show your LED panels in real-time, updating as modes cycle.

### Usage

#### Basic Usage

```bash
# Default: runs on localhost:8080
python emulator.py

# Custom port
python emulator.py --port 3000

# Allow external connections (access from other devices)
python emulator.py --host 0.0.0.0 --port 8080
```

#### Command Line Options

- `--port PORT` - Web server port (default: 8080)
- `--host HOST` - Web server host (default: localhost)
  - Use `localhost` for local-only access
  - Use `0.0.0.0` to allow connections from other devices on your network

### Interface

The emulator web interface includes:

#### Display Preview
- **Pixel-accurate rendering** at 5x scale for visibility
- **Automatic refresh** every second
- **Panel indicators** showing the layout

#### Live Statistics
- **Status** - Connection state
- **Frames Rendered** - Total frames displayed
- **Data Transferred** - Total bytes sent to display
- **Last Update** - Timestamp of most recent update

### Configuration

The emulator automatically uses your existing `config.yml` settings:

```yaml
display:
  ipixel:
    # Emulator will match these dimensions
    size_width: 64      # Width per panel
    size_height: 20     # Height per panel
    ble_addresses:      # Number of panels
      - "XX:XX:XX:XX:XX:XX"
      - "YY:YY:YY:YY:YY:YY"
```

**Display Dimensions:**
- Width = `size_width × number of panels`
- Height = `size_height`

**Example:** 2 panels of 64×20 = 128×20 total display

### Hot Reload Integration

The emulator works seamlessly with hot reload:

1. Start the emulator
2. Edit `config.yml` (change teams, intervals, etc.)
3. Save the file
4. Watch the changes appear instantly in your browser!

No restart needed - perfect for rapid iteration.

### Development Workflow

**Typical workflow:**

```bash
# Terminal 1: Start emulator
python emulator.py

# Terminal 2: Edit configuration
vim config.yml

# Browser: Watch live updates
# - Test different layouts
# - Preview team logos
# - Verify colors and spacing
# - Test animations
```

### Use Cases

#### Layout Design
- Test different `games_per_page` settings
- Preview logo sizes and positions
- Verify text fits within panel bounds

#### Color Tuning
- See team colors in action
- Adjust brightness and contrast
- Test readability

#### Animation Testing
- Preview ticker scrolling
- Test mode transitions
- Verify timing

#### Multi-Panel Layouts
- Visualize panel arrangement
- Test split content (ticker + static)
- Verify alignment

### Technical Details

#### Architecture
- **Adapter Pattern** - Implements the same interface as physical adapters
- **Web Server** - aiohttp-based HTTP server
- **Image Handling** - PIL/Pillow for image processing
- **Auto-Refresh** - JavaScript polls for updates every second

#### Performance
- **Low overhead** - Minimal impact on display manager
- **Efficient updates** - Only transfers changed images
- **Scalable** - Handles high frame rates

#### Image Rendering
- **Format:** PNG
- **Scaling:** 5x for visibility (configurable in CSS)
- **Filtering:** Pixelated (no smoothing for authentic look)

### Troubleshooting

#### Emulator Won't Start

**Check if aiohttp is installed:**
```bash
pip install aiohttp
```

**Port already in use:**
```bash
# Try a different port
python emulator.py --port 8081
```

**Check logs for errors:**
```bash
python emulator.py 2>&1 | tee emulator.log
```

#### Display Not Updating

**Verify browser connection:**
- Refresh the page (F5)
- Check browser console for errors (F12)

**Check emulator logs:**
- Look for "Frame X displayed" messages
- Verify modes are cycling

**Clear browser cache:**
- Hard refresh (Ctrl+Shift+R or Cmd+Shift+R)

#### Image Looks Wrong

**Verify configuration:**
- Check panel dimensions in config.yml
- Verify number of BLE addresses matches actual panels

**Check aspect ratio:**
- Emulator matches physical panel dimensions exactly

### Comparison: Emulator vs Physical Hardware

| Feature | Emulator | Physical Hardware |
|---------|----------|-------------------|
| Setup Time | Instant | Requires pairing |
| Visibility | Large, scaled display | Actual size |
| Testing Speed | Immediate | Upload delay |
| Portability | Run anywhere | Requires panels |
| Network | Not needed | BLE required |
| Cost | Free | Hardware cost |
| Use Case | Development/Testing | Production display |

### Best Practices

1. **Use emulator for development** - Iterate quickly without hardware wear
2. **Test on physical hardware** - Verify final appearance and performance
3. **Keep configs in sync** - Emulator uses same config.yml as production
4. **Document layouts** - Take screenshots of good designs
5. **Version control** - Commit working configurations

### Advanced Usage

#### Remote Access

Allow access from other devices on your network:

```bash
python emulator.py --host 0.0.0.0 --port 8080
```

Then access from any device:
```
http://your-computer-ip:8080
```

#### Development Mode

Run emulator alongside hot reload for maximum productivity:

```bash
# Emulator includes hot reload by default
python emulator.py

# Now edit config.yml and see instant updates!
```

#### Custom Styling

The emulator HTML can be customized by editing `adapters/emulator/adapter.py`.

Look for the `_generate_html()` method to modify:
- Colors and styling
- Layout and spacing
- Display scaling
- Additional features

### Examples

#### Testing Sports Layouts

```bash
# Start emulator
python emulator.py

# In config.yml, try different settings:
sports:
  games_per_page: 1  # Full screen
  show_logos: true   # With logos
  
# Save and see results immediately!

# Try 2 games per panel
sports:
  games_per_page: 2  # Compact mode
```

#### Previewing Team Changes

```bash
# In config.yml:
sports:
  teams:
    nba: ["UTA", "GSW", "LAL"]  # Change teams
    
# Save - new teams appear in emulator
# Verify logos load correctly
```

#### Testing Ticker Modes

```bash
# In config.yml:
ticker:
  modes: ["sports", "stocks"]
  scroll_speed: 3
  
# Watch ticker animation in emulator
# Adjust speed and see results
```

### FAQ

**Q: Does the emulator support GIF animations?**  
A: Currently shows first frame. Full GIF animation support coming soon.

**Q: Can I use emulator and physical panels simultaneously?**  
A: Not directly, but you can run two instances with different configs.

**Q: Does emulator work offline?**  
A: Yes! Only data fetching (sports, weather) requires internet.

**Q: Can I share emulator view with others?**  
A: Yes! Use `--host 0.0.0.0` and share your IP address.

**Q: Does emulator consume resources?**  
A: Minimal - just serves images. Display manager does the rendering.

### Future Enhancements

Planned features:
- [ ] Full GIF animation playback
- [ ] Side-by-side panel comparison
- [ ] Screenshot/recording capability
- [ ] Mobile-optimized interface
- [ ] Dark/light theme toggle
- [ ] Zoom controls
- [ ] Grid overlay option

### Feedback

Found a bug or have a feature request? The emulator is part of the LED Panel system - contributions welcome!

---

**Happy Developing! 🚀**

Use the emulator to perfect your displays before sending them to hardware.

