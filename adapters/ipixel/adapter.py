"""
BLE Display Adapter for iPixel LED panels.

This adapter implements the DisplayAdapter interface for BLE-connected iPixel LED panels.
It handles multi-panel configurations (1, 2, 3+ panels) and uses PNG upload for fast display updates.
"""
import asyncio
import logging
from typing import Optional, List

from bleak import BleakClient
from PIL import Image

from ..base import DisplayAdapter, ConnectionError, UploadError

logger = logging.getLogger('led_panel.adapter.ipixel')
from .protocol import (
    MultiPanelClient, _get_panel_addresses, set_panel_dimensions,
    clear_screen_completely, init_panels, upload_png, upload_gif, led_on, led_off
)


class BLEDisplayAdapter(DisplayAdapter):
    """
    BLE adapter for iPixel LED panels.

    Supports multi-panel configurations (1, 2, 3+) with PNG upload for instant display updates.
    Panel dimensions, count, and addresses are configured via config.yml.
    """

    def __init__(self):
        self.panel_clients: List[Optional[BleakClient]] = []
        self.client: Optional[MultiPanelClient] = None
        self._connected = False
        
        # Load panel dimensions from config
        self._load_panel_dimensions()
    
    def _load_panel_dimensions(self):
        """Load panel width and height from centralized config and configure protocol"""
        try:
            # Import from centralized config module
            from config import IPIXEL_PANEL_WIDTH, IPIXEL_PANEL_HEIGHT
            
            self.panel_width = IPIXEL_PANEL_WIDTH
            self.panel_height = IPIXEL_PANEL_HEIGHT
            
            # Configure protocol layer with these dimensions
            set_panel_dimensions(self.panel_width, self.panel_height)
            
        except Exception as e:
            # Fallback to defaults if config not available
            self.panel_width = 64
            self.panel_height = 20
            logger.warning(f"Failed to load panel dimensions, using defaults (64x20): {e}")
            set_panel_dimensions(64, 20)

    async def connect(self) -> None:
        """Establish BLE connections to all configured LED panels."""
        try:
            # Get configured panel addresses
            addresses = _get_panel_addresses()
            panel_count = len(addresses)
            
            logger.info(f"Connecting to {panel_count} LED panel(s)...")

            # Create and connect BLE clients for each panel
            for i, address in enumerate(addresses):
                client = BleakClient(address)
                await client.connect()
                self.panel_clients.append(client)
                logger.info(f"Connected to panel {i+1}/{panel_count}")

            logger.info(f"Connected to all {panel_count} panel(s)!")

            # Create multi-panel wrapper
            self.client = MultiPanelClient(self.panel_clients)

            # Initialize panels
            await init_panels(self.client)

            self._connected = True

        except Exception as e:
            self._connected = False
            raise ConnectionError(f"Failed to connect to BLE panels: {e}") from e

    async def disconnect(self) -> None:
        """Close BLE connections."""
        if self.client:
            await self.client.disconnect()
        self._connected = False
        logger.info("Disconnected from panels")

    async def upload_image(self, image, clear_first: bool = False, panels: list = None) -> None:
        """
        Upload PIL Image to panels using PNG upload.
        
        Args:
            image: PIL Image to display
            clear_first: Clear screen before uploading
            panels: List of panel indices (0-based). None or [] = all panels.
                    Example: [0] = panel 0, [0, 1] = panels 0 and 1
        """
        if not self._connected or not self.client:
            raise ConnectionError("Not connected to display")

        try:
            await upload_png(self.client, image, clear_first, panels)
        except Exception as e:
            raise UploadError(f"Failed to upload image: {e}") from e

    async def upload_gif(self, gif_path_or_data, clear_first: bool = False, max_frames: Optional[int] = None, panels: list = None) -> None:
        """
        Upload GIF animation to panels.
        
        Args:
            gif_path_or_data: Path to GIF file or bytes data
            clear_first: Clear screen before uploading
            max_frames: Maximum number of frames (None = all)
            panels: List of panel indices (0-based). None or [] = all panels.
                    Example: [0] = panel 0, [0, 1] = panels 0 and 1
        """
        if not self._connected or not self.client:
            raise ConnectionError("Not connected to display")

        try:
            await upload_gif(self.client, gif_path_or_data, clear_first, max_frames, panels)
        except Exception as e:
            raise UploadError(f"Failed to upload GIF: {e}") from e

    async def clear_screen(self) -> None:
        """Clear the display screens."""
        if not self._connected or not self.client:
            raise ConnectionError("Not connected to display")

        try:
            await clear_screen_completely(self.client)
        except Exception as e:
            raise UploadError(f"Failed to clear screen: {e}") from e

    async def power_on(self) -> None:
        """Turn the displays on."""
        if not self._connected or not self.client:
            raise ConnectionError("Not connected to display")

        try:
            await led_on(self.client)
        except Exception as e:
            raise UploadError(f"Failed to turn on display: {e}") from e

    async def power_off(self) -> None:
        """Turn the displays off."""
        if not self._connected or not self.client:
            raise ConnectionError("Not connected to display")

        try:
            await led_off(self.client)
        except Exception as e:
            raise UploadError(f"Failed to turn off display: {e}") from e

    @property
    def display_width(self) -> int:
        """Get total display width (same for all panels since they're stacked vertically)."""
        return self.panel_width

    @property
    def display_height(self) -> int:
        """Get total display height (stacked panels)."""
        if self.client:
            return self.panel_height * self.client.panel_count
        return self.panel_height  # Single panel default

    @property
    def is_connected(self) -> bool:
        """Check if connected to displays."""
        return self._connected

    async def get_info(self) -> dict:
        """Get adapter information."""
        return {
            "adapter_type": "ipixel",
            "device_count": 2,
            "panel_width": DISPLAY_WIDTH,
            "panel_height": DISPLAY_HEIGHT,
            "total_width": self.display_width,
            "total_height": self.display_height,
            "protocol": "iPixel BLE",
            "features": ["png_upload", "dual_panel", "fast_refresh"]
        }
