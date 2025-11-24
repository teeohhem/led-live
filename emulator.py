#!/usr/bin/env python3
"""
LED Panel Emulator - Run display manager with web-based virtual panels.

Usage:
    python emulator.py [--port 8080] [--host localhost]

This starts the display manager using the emulator adapter instead of physical hardware.
Open the URL shown in your browser to see the virtual LED panels.
"""
import asyncio
import argparse
import logging
import sys

# Setup logging before importing other modules
import logging_config

from adapters.emulator import EmulatorAdapter
from display_manager import DisplayManager
from config import (
    IPIXEL_PANEL_WIDTH,
    IPIXEL_PANEL_HEIGHT,
    IPIXEL_BLE_ADDRESSES,
)

logger = logging.getLogger('led_panel.emulator')


async def main(host='localhost', port=8080, panel_width=None, panel_height=None, num_panels=None, orientation='horizontal'):
    """Run display manager with emulator adapter."""
    # Use provided dimensions or fall back to config
    if panel_width is None:
        panel_width = IPIXEL_PANEL_WIDTH
    if panel_height is None:
        panel_height = IPIXEL_PANEL_HEIGHT
    if num_panels is None:
        num_panels = len(IPIXEL_BLE_ADDRESSES) if IPIXEL_BLE_ADDRESSES else 2
    
    # Calculate total display dimensions based on orientation
    if orientation.lower() in ['horizontal', 'h', 'horiz']:
        display_width = panel_width * num_panels
        display_height = panel_height
        orientation = 'horizontal'
    else:  # vertical
        display_width = panel_width
        display_height = panel_height * num_panels
        orientation = 'vertical'
    
    logger.info("=" * 60)
    logger.info("LED Panel Emulator")
    logger.info("=" * 60)
    logger.info(f"Display: {display_width}x{display_height} ({num_panels} panels)")
    logger.info(f"Panel size: {panel_width}x{panel_height}")
    logger.info(f"Orientation: {orientation}")
    logger.info(f"Web interface: http://{host}:{port}")
    logger.info("=" * 60)
    
    # Create emulator adapter with config
    config = {
        'display_width': display_width,
        'display_height': display_height,
        'num_panels': num_panels,
        'panel_width': panel_width,
        'panel_height': panel_height,
        'orientation': orientation,
        'emulator_host': host,
        'emulator_port': port,
    }
    
    adapter = EmulatorAdapter(config)
    
    try:
        # Connect (starts web server)
        await adapter.connect()
        await adapter.power_on()
        
        logger.info("")
        logger.info("✨ Emulator ready!")
        logger.info(f"   👉 Open http://{host}:{port} in your browser")
        logger.info("")
        logger.info("💡 Tips:")
        logger.info("   • Changes to config.yml will hot-reload automatically")
        logger.info("   • Press Ctrl+C to stop")
        logger.info("")
        
        # Create and run display manager
        manager = DisplayManager(adapter, enable_hot_reload=True)
        await manager.run()
        
    except KeyboardInterrupt:
        logger.info("\n")
        logger.info("Shutting down emulator...")
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        try:
            if adapter.is_connected:
                await adapter.disconnect()
        except:
            pass
    
    logger.info("Emulator stopped")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='LED Panel Emulator - Virtual display for testing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python emulator.py                              # Use config dimensions
  python emulator.py --port 3000                  # Custom port
  python emulator.py --host 0.0.0.0               # Allow external connections
  python emulator.py -w 32 -y 32                  # Custom panel size
  python emulator.py -p 4                         # 4 panels horizontal
  python emulator.py -p 3 --orientation vertical  # 3 panels stacked
  python emulator.py -w 64 -y 40 -p 3 -o h        # Full custom horizontal
        """
    )
    parser.add_argument(
        '--port',
        type=int,
        default=8080,
        help='Web server port (default: 8080)'
    )
    parser.add_argument(
        '--host',
        type=str,
        default='localhost',
        help='Web server host (default: localhost, use 0.0.0.0 for external access)'
    )
    parser.add_argument(
        '--width', '-w',
        type=int,
        default=None,
        help='Panel width in pixels (default: from config.yml)'
    )
    parser.add_argument(
        '--height', '-y',
        type=int,
        default=None,
        help='Panel height in pixels (default: from config.yml)'
    )
    parser.add_argument(
        '--panels', '-p',
        type=int,
        default=None,
        help='Number of panels (default: from config.yml)'
    )
    parser.add_argument(
        '--orientation', '-o',
        type=str,
        default='horizontal',
        choices=['horizontal', 'vertical', 'h', 'v'],
        help='Panel arrangement: horizontal (side-by-side) or vertical (stacked). Default: horizontal'
    )
    
    args = parser.parse_args()
    
    try:
        exit_code = asyncio.run(main(
            host=args.host,
            port=args.port,
            panel_width=args.width,
            panel_height=args.height,
            num_panels=args.panels,
            orientation=args.orientation
        ))
        sys.exit(exit_code)
    except KeyboardInterrupt:
        sys.exit(0)

