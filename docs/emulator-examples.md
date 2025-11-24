# Emulator Usage Examples

## Quick Reference

```bash
# Basic usage (uses config.yml dimensions)
python3 emulator.py

# Custom port
python3 emulator.py --port 3000

# Allow external connections
python3 emulator.py --host 0.0.0.0

# Custom dimensions
python3 emulator.py --width 32 --height 32

# Multiple panels
python3 emulator.py --panels 4

# Full custom setup
python3 emulator.py --width 64 --height 40 --panels 3
```

## Display Size Examples

### Small Display (32x32 single panel)
```bash
python3 emulator.py --width 32 --height 32 --panels 1
```
Perfect for: Testing compact layouts, single-panel designs

### Standard iPixel (64x20, 2 panels)
```bash
python3 emulator.py --width 64 --height 20 --panels 2
# Or just: python3 emulator.py (uses config.yml defaults)
```
Perfect for: Standard dual-panel setup (128x20 total)

### Square Display (40x40, 2 panels)
```bash
python3 emulator.py --width 40 --height 40 --panels 2
```
Perfect for: Square format displays (80x40 total)

### Large Display (64x32, 4 panels)
```bash
python3 emulator.py --width 64 --height 32 --panels 4
```
Perfect for: Large installations (256x32 total)

### Portrait Mode (20x64 vertical)
```bash
python3 emulator.py --width 20 --height 64 --panels 1
```
Perfect for: Vertical displays

### Ultra-Wide (64x20, 4 panels)
```bash
python3 emulator.py --width 64 --height 20 --panels 4
```
Perfect for: Extra-wide ticker displays (256x20 total)

## Network Access Examples

### Local Only (Default)
```bash
python3 emulator.py
# Access: http://localhost:8080
```

### Local Network Access
```bash
python3 emulator.py --host 0.0.0.0 --port 8080
# Access from any device: http://YOUR_IP:8080
```

### Custom Port
```bash
python3 emulator.py --port 3000
# Access: http://localhost:3000
```

### Remote Access with Custom Port
```bash
python3 emulator.py --host 0.0.0.0 --port 8888
# Access from phone/tablet: http://YOUR_COMPUTER_IP:8888
```

## Development Workflows

### Testing Different Layouts
```bash
# Test compact layout
python3 emulator.py --width 32 --height 16 --panels 2

# Test standard layout
python3 emulator.py --width 64 --height 20 --panels 2

# Test large layout
python3 emulator.py --width 64 --height 32 --panels 3
```

### Multi-Device Testing
```bash
# On your computer
python3 emulator.py --host 0.0.0.0 --port 8080

# Then access from:
# - Phone: http://192.168.1.100:8080
# - Tablet: http://192.168.1.100:8080
# - Another computer: http://192.168.1.100:8080
```

### Quick Prototype Testing
```bash
# Start with small display for rapid iteration
python3 emulator.py -w 32 -h 16 -p 1

# Scale up when ready
python3 emulator.py -w 64 -h 32 -p 2
```

## Common Configurations

### Raspberry Pi Matrix Displays

**32x32 RGB Matrix**
```bash
python3 emulator.py --width 32 --height 32 --panels 1
```

**64x32 RGB Matrix**
```bash
python3 emulator.py --width 64 --height 32 --panels 1
```

**64x64 RGB Matrix (2x 64x32)**
```bash
python3 emulator.py --width 64 --height 32 --panels 2
```

### iPixel Configurations

**Single Panel**
```bash
python3 emulator.py --width 64 --height 20 --panels 1
```

**Dual Panel (Standard)**
```bash
python3 emulator.py --width 64 --height 20 --panels 2
```

**Triple Panel**
```bash
python3 emulator.py --width 64 --height 20 --panels 3
```

**Quad Panel**
```bash
python3 emulator.py --width 64 --height 20 --panels 4
```

### Custom Displays

**16:9 Aspect Ratio (64x36)**
```bash
python3 emulator.py --width 64 --height 36 --panels 2
```

**Square Multi-Panel (32x32 each, 4 panels)**
```bash
python3 emulator.py --width 32 --height 32 --panels 4
```

**Extra Tall (32x64)**
```bash
python3 emulator.py --width 32 --height 64 --panels 1
```

## Tips

### Finding Your Computer's IP Address

**macOS / Linux:**
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

**Windows:**
```bash
ipconfig
```

### Testing Responsive Layouts

Test how your content looks at different sizes:
```bash
# Small
python3 emulator.py -w 32 -h 16 -p 1

# Medium  
python3 emulator.py -w 64 -h 32 -p 2

# Large
python3 emulator.py -w 64 -h 40 -p 4
```

### Performance Testing

Test with many panels to see performance:
```bash
python3 emulator.py --width 64 --height 32 --panels 8
# Total: 512x32 (16,384 pixels)
```

### Portrait vs Landscape

**Landscape (default)**
```bash
python3 emulator.py --width 64 --height 20 --panels 2
# 128x20 (wide)
```

**Portrait**
```bash
python3 emulator.py --width 20 --height 64 --panels 1
# 20x64 (tall)
```

## Shorthand Flags

All arguments have short versions:
- `--width` = `-w`
- `--height` = `-y`  
- `--panels` = `-p`

Note: `-h` is reserved for `--help`

```bash
# These are equivalent:
python3 emulator.py --width 64 --height 32 --panels 3
python3 emulator.py -w 64 -y 32 -p 3
```

## Common Issues

### Port Already in Use
```bash
# Try a different port
python3 emulator.py --port 8081
```

### Can't Connect from Other Devices
```bash
# Make sure to use 0.0.0.0 as host
python3 emulator.py --host 0.0.0.0

# Check firewall settings
# Make sure port 8080 is allowed
```

### Display Too Small/Large
```bash
# Adjust dimensions to match your needs
python3 emulator.py --width 48 --height 24 --panels 2
```

## Advanced Usage

### Multiple Emulators (Different Ports)
```bash
# Terminal 1: Small display
python3 emulator.py --port 8080 -w 32 -h 16 -p 1

# Terminal 2: Large display  
python3 emulator.py --port 8081 -w 64 -h 32 -p 4
```

### Quick Dimension Presets

Create shell aliases for common sizes:

```bash
# Add to ~/.bashrc or ~/.zshrc
alias emu-small='python3 emulator.py -w 32 -h 16 -p 1'
alias emu-medium='python3 emulator.py -w 64 -h 20 -p 2'
alias emu-large='python3 emulator.py -w 64 -h 32 -p 4'

# Usage:
emu-small
emu-medium  
emu-large
```

## Help Command

See all options:
```bash
python3 emulator.py --help
```

Output:
```
usage: emulator.py [-h] [--port PORT] [--host HOST] [--width WIDTH] 
                   [--height HEIGHT] [--panels PANELS]

LED Panel Emulator - Virtual display for testing

optional arguments:
  -h, --help            show this help message and exit
  --port PORT           Web server port (default: 8080)
  --host HOST           Web server host (default: localhost)
  --width WIDTH, -w WIDTH
                        Panel width in pixels (default: from config.yml)
  --height HEIGHT, -h HEIGHT
                        Panel height in pixels (default: from config.yml)
  --panels PANELS, -p PANELS
                        Number of panels (default: from config.yml)
```

