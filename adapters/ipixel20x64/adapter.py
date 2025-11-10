"""
BLE Display Adapter for iPixel LED panels.

This adapter implements the DisplayAdapter interface for BLE-connected iPixel LED panels.
It handles dual-panel configurations and uses PNG upload for fast display updates.
"""
import asyncio
from typing import Optional

try:
    from bleak import BleakClient
    BLEAK_AVAILABLE = True
except ImportError:
    BLEAK_AVAILABLE = False
    BleakClient = None

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None

from ..base import DisplayAdapter, ConnectionError, UploadError
from .protocol import (
    DualPanelClient, BLE_ADDRESS_TOP, BLE_ADDRESS_BOTTOM,
    DISPLAY_WIDTH, DISPLAY_HEIGHT,
    clear_screen_completely, init_panels, upload_png, led_on, led_off
)


class BLEDisplayAdapter(DisplayAdapter):
    """
    BLE adapter for iPixel LED panels.

    Supports dual-panel configurations with PNG upload for instant display updates.
    """

    def __init__(self):
        self.top_client: Optional[BleakClient] = None
        self.bottom_client: Optional[BleakClient] = None
        self.client: Optional[DualPanelClient] = None
        self._connected = False

    async def connect(self) -> None:
        """Establish BLE connections to LED panels."""
        if not BLEAK_AVAILABLE:
            raise ConnectionError("BLE functionality requires 'bleak' library. Install with: pip install bleak")

        try:
            print("🔗 Connecting to LED panels...")

            # Create BLE clients
            self.top_client = BleakClient(BLE_ADDRESS_TOP)
            self.bottom_client = BleakClient(BLE_ADDRESS_BOTTOM)

            # Connect to both panels
            await self.top_client.connect()
            await self.bottom_client.connect()

            print("✅ Connected to both panels!")

            # Create dual panel wrapper
            self.client = DualPanelClient(self.top_client, self.bottom_client)

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
        print("🔌 Disconnected from panels")

    async def upload_image(self, image, clear_first: bool = False) -> None:
        """Upload PIL Image to panels using PNG upload."""
        if not PIL_AVAILABLE:
            raise UploadError("Image upload requires 'PIL' (Pillow) library. Install with: pip install Pillow")

        if not self._connected or not self.client:
            raise ConnectionError("Not connected to display")

        try:
            await upload_png(self.client, image, clear_first)
        except Exception as e:
            raise UploadError(f"Failed to upload image: {e}") from e

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
        """Get total display width."""
        return DISPLAY_WIDTH

    @property
    def display_height(self) -> int:
        """Get total display height."""
        return DISPLAY_HEIGHT

    @property
    def is_connected(self) -> bool:
        """Check if connected to displays."""
        return self._connected

    async def get_info(self) -> dict:
        """Get adapter information."""
        return {
            "adapter_type": "ipixel20x64",
            "device_count": 2,
            "panel_width": DISPLAY_WIDTH,
            "panel_height": DISPLAY_HEIGHT,
            "total_width": self.display_width,
            "total_height": self.display_height,
            "protocol": "iPixel BLE",
            "features": ["png_upload", "dual_panel", "fast_refresh"]
        }
