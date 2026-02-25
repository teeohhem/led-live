"""
BLE Display Adapter for iPixel LED panels.

This adapter implements the DisplayAdapter interface for BLE-connected iPixel LED panels.
It handles multi-panel configurations (1, 2, 3+ panels) and uses PNG upload for fast display updates.
"""
import asyncio
import logging
from typing import Optional, List

from bleak import BleakClient, BleakScanner
from bleak.exc import BleakError

from ..base import DisplayAdapter, ConnectionError, UploadError
from .protocol import (
    MultiPanelClient, _get_panel_addresses, set_panel_dimensions,
    clear_screen_completely, init_panels, upload_png, upload_gif, led_on, led_off
)

logger = logging.getLogger('led_panel.adapter.ipixel')


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
    
    def _load_panel_dimensions(self) -> None:
        """Load panel width and height from centralized config and configure protocol."""
        try:
            from config import IPIXEL_PANEL_WIDTH, IPIXEL_PANEL_HEIGHT
            
            self.panel_width = IPIXEL_PANEL_WIDTH
            self.panel_height = IPIXEL_PANEL_HEIGHT
            set_panel_dimensions(self.panel_width, self.panel_height)
            
        except Exception as e:
            # Fallback to defaults if config not available
            self.panel_width = 64
            self.panel_height = 20
            logger.warning(f"Failed to load panel dimensions, using defaults (64x20): {e}")
            set_panel_dimensions(64, 20)

    # Scan timeout in seconds; one discover() is used for all panels to avoid repeated scanner start/stop
    DISCOVER_TIMEOUT = 15

    async def _attempt_panel_connections(
        self,
        addresses: List[str],
        panel_indices: List[int],
        connected_clients: List[Optional[BleakClient]],
    ) -> List[int]:
        """
        Discover BLE devices once, then connect to each panel from the same result set.
        Single scan per connect() reduces CoreBluetooth state issues on macOS.
        """
        panel_count = len(addresses)
        failed_indices = []

        logger.info(f"Discovering BLE devices ({self.DISCOVER_TIMEOUT}s)...")
        try:
            devices = await BleakScanner.discover(timeout=self.DISCOVER_TIMEOUT)
        except BleakError as e:
            if "not authorized" in str(e).lower() or "unauthorized" in str(e).lower():
                raise PermissionError(
                    "BLE is not authorized — macOS has denied Bluetooth access to this process.\n"
                    "\n"
                    "To fix:\n"
                    "  1. Open System Settings → Privacy & Security → Bluetooth\n"
                    "  2. Ensure Terminal (or Python) is listed and toggled ON\n"
                    "  3. If missing, run the script from Terminal once so macOS prompts for permission\n"
                    "  4. If running under launchd/a daemon, the daemon user also needs this grant\n"
                    "\n"
                    "This permission is sometimes silently revoked after a macOS update, sleep/wake\n"
                    "cycle, or background privacy-policy refresh. Re-granting it is the only fix."
                ) from e
            raise
        # Case-insensitive address lookup (UUIDs may differ in casing)
        address_to_device = {}
        for d in devices:
            address_to_device[d.address.upper()] = d

        for panel_idx in panel_indices:
            address = addresses[panel_idx]
            key = address.upper()
            device = address_to_device.get(key)
            if device is None:
                logger.warning(
                    f"Panel {panel_idx+1}/{panel_count} not found during scan: {address}"
                )
                failed_indices.append(panel_idx)
                continue
            try:
                client = BleakClient(device)
                await client.connect()
                connected_clients[panel_idx] = client
                logger.info(f"Connected to panel {panel_idx+1}/{panel_count}")
            except Exception as e:
                logger.warning(
                    f"Panel {panel_idx+1}/{panel_count} connection failed: {e}"
                )
                failed_indices.append(panel_idx)

        return failed_indices
    
    def _finalize_connection(self, connected_clients: List[Optional[BleakClient]], panel_count: int) -> None:
        """
        Finalize connection setup after panels are connected.
        
        Args:
            connected_clients: List of connected clients (may contain None)
            panel_count: Total number of panels
        """
        self.panel_clients = connected_clients
        self.client = MultiPanelClient(self.panel_clients)
        self._connected = True
        
        connected_count = sum(1 for c in connected_clients if c is not None)
        if connected_count == panel_count:
            logger.info(f"Connected to all {panel_count} panel(s)!")
        else:
            logger.warning(f"Connected to {connected_count}/{panel_count} panel(s)")
    
    async def connect(self) -> None:
        """
        Establish BLE connections to all configured LED panels (single attempt).
        
        Supports partial connections - will continue with available panels if some fail.
        Retries are handled by the display loop (ensure_connected every 60s) rather than blocking here.
        
        Raises:
            ConnectionError: If no panels could be connected
        """
        addresses = _get_panel_addresses()
        panel_count = len(addresses)
        
        logger.info(f"Connecting to {panel_count} LED panel(s)...")
        
        connected_clients: List[Optional[BleakClient]] = [None] * panel_count
        failed_panels = await self._attempt_panel_connections(
            addresses, list(range(panel_count)), connected_clients
        )
        
        if not failed_panels:
            self._finalize_connection(connected_clients, panel_count)
            await init_panels(self.client)
            return
        
        connected_count = sum(1 for c in connected_clients if c is not None)
        if connected_count > 0:
            logger.warning(f"Failed to connect to {len(failed_panels)} panel(s), continuing with {connected_count}")
            self._finalize_connection(connected_clients, panel_count)
            await init_panels(self.client)
            return
        
        # Complete failure - no panels connected
        logger.error(f"Failed to connect to all {panel_count} panel(s)")
        self.panel_clients = []
        self.client = None
        self._connected = False
        raise ConnectionError("Failed to connect to BLE panels")

    async def disconnect(self) -> None:
        """Close BLE connections to all panels and clear state for clean reconnect."""
        if self.client:
            await self.client.disconnect()
        self.panel_clients = []
        self.client = None
        self._connected = False
        logger.info("Disconnected from panels")
    
    def _count_healthy_panels(self) -> int:
        """
        Count the number of panels that are still connected.
        
        Returns:
            Number of healthy panels
        """
        healthy_count = 0
        for i, client in enumerate(self.panel_clients):
            try:
                if client and client.is_connected:
                    healthy_count += 1
            except Exception as e:
                logger.debug(f"Panel {i+1} health check failed: {e}")
        return healthy_count
    
    async def ensure_connected(self) -> bool:
        """
        Check if all panels are connected. If any disconnected, reset and reconnect all.
        
        Returns:
            True if all panels connected successfully, False otherwise.
        
        Note:
            On any disconnect, this will cleanly disconnect ALL panels and attempt
            a fresh reconnection to all panels. This ensures a clean state.
        """
        if not self._connected or not self.client:
            logger.warning("Not connected - attempting reconnection")
            try:
                await self.connect()
                return True
            except ConnectionError as e:
                logger.error(f"Reconnection failed: {e}")
                return False
        
        # Check if all panels are healthy
        total_panels = len(self.panel_clients)
        healthy_count = self._count_healthy_panels()
        
        if healthy_count == total_panels:
            logger.debug(f"All {total_panels} panel(s) healthy")
            return True
        
        # Some panel(s) disconnected - reset everything
        logger.warning(
            f"Panel disconnect detected ({healthy_count}/{total_panels} healthy). "
            f"Resetting and reconnecting all panels..."
        )
        
        # Cleanly disconnect all panels
        try:
            await self.disconnect()
        except Exception as e:
            logger.warning(f"Error during disconnect: {e}")
        
        # Delay to let BLE resources fully release and devices become discoverable
        await asyncio.sleep(4.0)
        
        # Attempt fresh reconnection
        try:
            await self.connect()
            logger.info("Successfully reconnected all panels")
            return True
        except ConnectionError as e:
            logger.error(f"Reconnection failed: {e}")
            return False

    async def upload_image(self, image, clear_first: bool = False, panels: Optional[List[int]] = None) -> None:
        """
        Upload PIL Image to panels using PNG upload.
        
        Args:
            image: PIL Image to display
            clear_first: Clear screen before uploading
            panels: List of panel indices (0-based). None or [] = all panels.
                    Example: [0] = panel 0, [0, 1] = panels 0 and 1
        
        Raises:
            ConnectionError: If not connected to display
        
        Note:
            On BLE error, marks connection as failed to trigger reconnection on next ensure_connected().
        """
        if not self._connected or not self.client:
            raise ConnectionError("Not connected to display")

        try:
            await upload_png(self.client, image, clear_first, panels)
        except BleakError as e:
            logger.error(f"BLE error during upload: {e}")
            # Mark as disconnected to trigger reconnection
            self._connected = False
            raise UploadError(f"Upload failed: {e}")
        except Exception as e:
            logger.error(f"Upload error: {e}")
            raise UploadError(f"Upload failed: {e}")

    async def upload_gif(
        self, 
        gif_path_or_data, 
        clear_first: bool = False, 
        max_frames: Optional[int] = None, 
        panels: Optional[List[int]] = None
    ) -> None:
        """
        Upload GIF animation to panels.
        
        Args:
            gif_path_or_data: Path to GIF file or bytes data
            clear_first: Clear screen before uploading
            max_frames: Maximum number of frames (None = all)
            panels: List of panel indices (0-based). None or [] = all panels.
                    Example: [0] = panel 0, [0, 1] = panels 0 and 1
        
        Raises:
            ConnectionError: If not connected to display
        
        Note:
            On BLE error, marks connection as failed to trigger reconnection on next ensure_connected().
        """
        if not self._connected or not self.client:
            raise ConnectionError("Not connected to display")

        try:
            await upload_gif(self.client, gif_path_or_data, clear_first, max_frames, panels)
        except BleakError as e:
            logger.error(f"BLE error during GIF upload: {e}")
            # Mark as disconnected to trigger reconnection
            self._connected = False
            raise UploadError(f"GIF upload failed: {e}")
        except Exception as e:
            logger.error(f"GIF upload error: {e}")
            raise UploadError(f"GIF upload failed: {e}")

    async def clear_screen(self) -> None:
        """
        Clear all display screens.
        
        Raises:
            ConnectionError: If not connected to display
            UploadError: If clear operation fails
        """
        if not self._connected or not self.client:
            raise ConnectionError("Not connected to display")

        try:
            await clear_screen_completely(self.client)
        except Exception as e:
            raise UploadError(f"Failed to clear screen: {e}") from e

    async def power_on(self) -> None:
        """
        Turn all displays on.
        
        Raises:
            ConnectionError: If not connected to display
            UploadError: If power on operation fails
        """
        if not self._connected or not self.client:
            raise ConnectionError("Not connected to display")

        try:
            await led_on(self.client)
        except Exception as e:
            raise UploadError(f"Failed to turn on display: {e}") from e

    async def power_off(self) -> None:
        """
        Turn all displays off.
        
        Raises:
            ConnectionError: If not connected to display
            UploadError: If power off operation fails
        """
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
        """
        Get adapter information.
        
        Returns:
            Dictionary with adapter configuration and capabilities
        """
        panel_count = len(self.panel_clients) if self.panel_clients else 0
        return {
            "adapter_type": "ipixel",
            "device_count": panel_count,
            "panel_width": self.panel_width,
            "panel_height": self.panel_height,
            "total_width": self.display_width,
            "total_height": self.display_height,
            "protocol": "iPixel BLE",
            "features": ["png_upload", "multi_panel", "fast_refresh"]
        }
