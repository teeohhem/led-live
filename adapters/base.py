"""
Base DisplayAdapter interface for LED panel display protocols.

This abstract base class defines the interface that all display adapters must implement.
Display adapters handle the communication protocol with LED panels, allowing the rest
of the system to work with different display types (BLE, WiFi, serial, etc.) through
a common interface.
"""
from abc import ABC, abstractmethod
from typing import Optional

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    # Create a dummy Image class for type hints when PIL is not available
    class Image:
        pass


class DisplayAdapter(ABC):
    """
    Abstract base class for display adapters.

    All display adapters must inherit from this class and implement all abstract methods.
    This ensures consistent behavior across different display protocols.
    """

    @abstractmethod
    async def connect(self) -> None:
        """
        Establish connection to the display device(s).

        This method should handle all necessary connection setup, including:
        - Discovering devices
        - Establishing communication channels
        - Initializing device state
        - Setting up connection pooling if needed

        Raises:
            ConnectionError: If connection cannot be established
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """
        Close connection to the display device(s).

        This method should properly clean up all connections and resources.
        """
        pass

    @abstractmethod
    async def upload_image(self, image: Image, clear_first: bool = False) -> None:
        """
        Upload a PIL Image to the display device(s).

        Args:
            image: PIL Image to display (RGB mode)
            clear_first: If True, clear screen before uploading

        The adapter should handle:
        - Image format conversion if needed
        - Splitting large images across multiple panels
        - Protocol-specific packet formatting
        - Error handling and retries

        Raises:
            DisplayError: If upload fails
        """
        pass

    @abstractmethod
    async def clear_screen(self) -> None:
        """
        Clear the display screen(s).

        This should reset all pixels to off/black state.
        """
        pass

    @abstractmethod
    async def power_on(self) -> None:
        """
        Turn the display device(s) on.

        This should wake the display from sleep/standby mode.
        """
        pass

    @abstractmethod
    async def power_off(self) -> None:
        """
        Turn the display device(s) off.

        This should put the display into sleep/standby mode.
        """
        pass

    @property
    @abstractmethod
    def display_width(self) -> int:
        """
        Get the total display width in pixels.

        For multi-panel setups, this should be the combined width.
        """
        pass

    @property
    @abstractmethod
    def display_height(self) -> int:
        """
        Get the total display height in pixels.

        For multi-panel setups, this should be the combined height.
        """
        pass

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """
        Check if the display is currently connected.

        Returns:
            True if connected and ready to receive commands
        """
        pass

    @abstractmethod
    async def get_info(self) -> dict:
        """
        Get information about the display adapter and connected devices.

        Returns:
            Dictionary with adapter information such as:
            - adapter_type: "ble", "wifi", etc.
            - device_count: number of panels
            - firmware_version: if available
            - connection_strength: signal quality
        """
        pass


class DisplayError(Exception):
    """Base exception for display adapter errors."""
    pass


class ConnectionError(DisplayError):
    """Raised when connection to display fails."""
    pass


class UploadError(DisplayError):
    """Raised when image upload fails."""
    pass
