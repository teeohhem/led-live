"""
BLE Display Adapter for iPixel LED panels.

This adapter implements the DisplayAdapter interface for BLE-connected iPixel LED panels.
It handles multi-panel configurations (1, 2, 3+ panels) and uses PNG upload for fast display updates.
"""
import asyncio
import logging
from typing import Optional, List

from bleak import BleakClient
from bleak.exc import BleakError
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
        self._connection_attempts = 0
        self._max_retries = 5
        
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
        """Establish BLE connections to all configured LED panels with exponential backoff retry."""
        retry_count = 0
        last_error = None
        
        while retry_count <= self._max_retries:
            try:
                # Get configured panel addresses
                addresses = _get_panel_addresses()
                panel_count = len(addresses)
                
                if retry_count > 0:
                    logger.info(f"Retry {retry_count}/{self._max_retries} - Connecting to {panel_count} LED panel(s)...")
                else:
                    logger.info(f"Connecting to {panel_count} LED panel(s)...")

                # Clear any existing clients
                self.panel_clients = []

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
                self._connection_attempts = 0  # Reset on successful connection
                return  # Success!

            except Exception as e:
                last_error = e
                retry_count += 1
                self._connected = False
                
                # Cleanup any partial connections
                for client in self.panel_clients:
                    try:
                        if client.is_connected:
                            await client.disconnect()
                    except:
                        pass
                self.panel_clients = []
                
                if retry_count <= self._max_retries:
                    # Exponential backoff: 2^retry seconds (2, 4, 8, 16, 32 seconds)
                    wait_time = min(2 ** retry_count, 32)
                    logger.warning(f"Connection failed: {e}")
                    logger.info(f"Waiting {wait_time} seconds before retry...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Failed to connect after {self._max_retries} retries")
                    raise ConnectionError(f"Failed to connect to BLE panels after {self._max_retries} retries: {last_error}") from last_error

    async def disconnect(self) -> None:
        """Close BLE connections."""
        if self.client:
            await self.client.disconnect()
        self._connected = False
        logger.info("Disconnected from panels")
    
    async def _check_connection_health(self) -> bool:
        """Check if BLE connection is still alive."""
        if not self._connected or not self.client:
            return False
        
        try:
            # Check if all panel clients are still connected
            for client in self.panel_clients:
                if not client.is_connected:
                    logger.warning("Panel client disconnected")
                    return False
            return True
        except Exception as e:
            logger.warning(f"Connection health check failed: {e}")
            return False
    
    async def _auto_reconnect(self) -> bool:
        """
        Attempt to reconnect with exponential backoff.
        Returns True if reconnection successful, False otherwise.
        """
        logger.warning("Connection lost - attempting to reconnect...")
        self._connected = False
        
        try:
            await self.connect()
            logger.info("Reconnection successful!")
            return True
        except Exception as e:
            logger.error(f"Reconnection failed: {e}")
            return False

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
        except BleakError as e:
            # BLE-specific errors might indicate connection loss
            logger.error(f"BLE error during upload: {e}")
            
            # Check if it's a connection-related error
            error_msg = str(e).lower()
            if any(keyword in error_msg for keyword in ['service discovery', 'not connected', 'disconnected', 'connection']):
                logger.warning("Detected connection issue - attempting reconnection...")
                if await self._auto_reconnect():
                    # Retry upload after successful reconnection
                    logger.info("Retrying upload after reconnection...")
                    try:
                        await upload_png(self.client, image, clear_first, panels)
                        logger.info("Upload successful after reconnection")
                        return
                    except Exception as retry_error:
                        raise UploadError(f"Failed to upload image after reconnection: {retry_error}") from retry_error
                else:
                    raise ConnectionError(f"Connection lost and reconnection failed: {e}") from e
            else:
                raise UploadError(f"Failed to upload image: {e}") from e
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
        except BleakError as e:
            # BLE-specific errors might indicate connection loss
            logger.error(f"BLE error during GIF upload: {e}")
            
            # Check if it's a connection-related error
            error_msg = str(e).lower()
            if any(keyword in error_msg for keyword in ['service discovery', 'not connected', 'disconnected', 'connection']):
                logger.warning("Detected connection issue - attempting reconnection...")
                if await self._auto_reconnect():
                    # Retry upload after successful reconnection
                    logger.info("Retrying GIF upload after reconnection...")
                    try:
                        await upload_gif(self.client, gif_path_or_data, clear_first, max_frames, panels)
                        logger.info("GIF upload successful after reconnection")
                        return
                    except Exception as retry_error:
                        raise UploadError(f"Failed to upload GIF after reconnection: {retry_error}") from retry_error
                else:
                    raise ConnectionError(f"Connection lost and reconnection failed: {e}") from e
            else:
                raise UploadError(f"Failed to upload GIF: {e}") from e
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
