"""
Core panel functionality - MODERN PNG-BASED RENDERING
======================================================

This module provides BLE communication and PNG upload for instant display updates.

Key Features:
- Dual-panel support (64x40 pixels via two 64x20 panels)
- PNG upload for instant full-screen rendering (< 1 second)
- Clean BLE connection management
- Screen clearing and initialization

LEGACY CODE ARCHIVED:
Old pixel-by-pixel rendering functions have been moved to legacy/legacy_utils.py
They were very slow (10-60 seconds) and are no longer used.

Modern approach: Use PIL to draw everything, then upload_png() for instant display!

Shared by all display applications (sports, weather, clock, etc.)
"""
import asyncio
import io
import os
import zlib
from pathlib import Path
from PIL import Image

# Load environment variables from config.env if it exists
config_file = Path(__file__).parent / "config.env"
if config_file.exists():
    with open(config_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip())

# --- BLE / Panel settings ---
UUID_WRITE_DATA = os.getenv(
    "BLE_UUID_WRITE", 
    "0000fa02-0000-1000-8000-00805f9b34fb"
)

# Display dimensions (configurable)
PANEL_WIDTH = int(os.getenv("PANEL_WIDTH", "64"))
PANEL_HEIGHT = int(os.getenv("PANEL_HEIGHT", "20"))
PANEL_COUNT = int(os.getenv("PANEL_COUNT", "2"))

# Calculated dimensions
DISPLAY_WIDTH = PANEL_WIDTH
DISPLAY_HEIGHT = PANEL_HEIGHT * PANEL_COUNT

# Dual panel BLE addresses (configure in config.env)
BLE_ADDRESS_TOP = os.getenv(
    "BLE_ADDRESS_TOP",
    "YOUR-TOP-PANEL-BLE-ADDRESS"  # Replace or set in config.env
)
BLE_ADDRESS_BOTTOM = os.getenv(
    "BLE_ADDRESS_BOTTOM",
    "YOUR-BOTTOM-PANEL-BLE-ADDRESS"  # Replace or set in config.env
)

# --- BLE Commands ---
SCREEN_ON = bytearray([5, 0, 7, 1, 1])
SCREEN_OFF = bytearray([5, 0, 7, 1, 0])
CLEAR_SCREEN = bytearray([5, 0, 8, 1, 1])


# --- Dual Panel Client Wrapper ---
class DualPanelClient:
    """Wrapper for dual panel setup that routes commands to the correct panel"""
    def __init__(self, top_client, bottom_client):
        self.top_client = top_client
        self.bottom_client = bottom_client
    
    async def write_gatt_char(self, uuid, data, response=False):
        """Route write commands to appropriate panel based on pixel Y coordinate"""
        await self.top_client.write_gatt_char(uuid, data, response=response)
    
    async def connect(self):
        """Both panels should already be connected"""
        pass
    
    async def disconnect(self):
        """Disconnect both panels"""
        await self.top_client.disconnect()
        await self.bottom_client.disconnect()


# --- BLE write helper ---
async def write_cmd(client, data: bytes):
    """
    Write command to client with proper chunking (like idotmatrix library does).
    Chunks data based on MTU size for reliable transmission.
    """
    import time
    
    if isinstance(client, DualPanelClient):
        # Send to top panel with chunking
        try:
            chunk_size_top = client.top_client.services.get_characteristic(UUID_WRITE_DATA).max_write_without_response_size
        except:
            chunk_size_top = 512  # Default fallback
        for i in range(0, len(data), chunk_size_top):
            await client.top_client.write_gatt_char(UUID_WRITE_DATA, data[i:i+chunk_size_top], response=False)
        
        # Send to bottom panel with chunking
        try:
            chunk_size_bottom = client.bottom_client.services.get_characteristic(UUID_WRITE_DATA).max_write_without_response_size
        except:
            chunk_size_bottom = 512  # Default fallback
        for i in range(0, len(data), chunk_size_bottom):
            await client.bottom_client.write_gatt_char(UUID_WRITE_DATA, data[i:i+chunk_size_bottom], response=False)
    else:
        # Single client with chunking
        try:
            chunk_size = client.services.get_characteristic(UUID_WRITE_DATA).max_write_without_response_size
        except:
            chunk_size = 512  # Default fallback
        for i in range(0, len(data), chunk_size):
            await client.write_gatt_char(UUID_WRITE_DATA, data[i:i+chunk_size], response=False)
    
    # Small delay like idotmatrix library does
    time.sleep(0.01)


# --- Text rendering helpers ---
# --- LEGACY pixel-by-pixel functions moved to legacy/legacy_utils.py ---
# Modern code uses PNG upload (see upload_png function below) for instant updates!


# --- Screen management ---
async def clear_screen_completely(client):
    """Clear the screen by sending clear command (dual-panel compatible)"""
    print("🔄 Clearing panels...")
    try:
        await write_cmd(client, CLEAR_SCREEN)
        await asyncio.sleep(0.3)
        print("✅ Panels cleared")
    except Exception as e:
        print(f"❌ Clear failed: {e}")


async def init_panels(client):
    """Initialize panels after connection"""
    print("✅ Both panels connected, initializing...")
    await write_cmd(client, SCREEN_ON)
    await asyncio.sleep(0.2)
    print("✅ Both panels initialized")


# --- PNG Upload (FAST display updates!) ---
def create_png_packet(image):
    """
    Convert PIL Image to panel upload packet (PNG format).
    This is the FASTEST way to update the display - entire frame in one command!
    
    Args:
        image: PIL Image (RGB mode, typically 64x20 for single panel or 64x40 for dual)
    
    Returns:
        bytearray: Complete packet ready to send
    """
    # Convert image to PNG in memory
    png_buffer = io.BytesIO()
    image.save(png_buffer, format='PNG', optimize=False)
    png_data = png_buffer.getvalue()
    
    # Calculate CRC32 of PNG data
    crc = zlib.crc32(png_data) & 0xFFFFFFFF
    
    # Build packet header (15 bytes)
    png_len = len(png_data)
    total_len = png_len + 15  # PNG data + 15-byte header
    
    header = bytearray([
        total_len & 0xFF,           # Total length (low byte)
        (total_len >> 8) & 0xFF,    # Total length (high byte)
        0x02, 0x00,                 # Command: 0x0002 (image upload)
        0x00,                       # Unknown
        png_len & 0xFF,             # PNG length (byte 0)
        (png_len >> 8) & 0xFF,      # PNG length (byte 1)
        (png_len >> 16) & 0xFF,     # PNG length (byte 2)
        (png_len >> 24) & 0xFF,     # PNG length (byte 3)
        crc & 0xFF,                 # CRC32 (byte 0)
        (crc >> 8) & 0xFF,          # CRC32 (byte 1)
        (crc >> 16) & 0xFF,         # CRC32 (byte 2)
        (crc >> 24) & 0xFF,         # CRC32 (byte 3)
        0x00, 0x2F,                 # Flags from iOS app capture
    ])
    
    return header + png_data


async def upload_png(client, image, clear_first=False):
    """
    Upload a PIL Image to panel(s) using PNG upload (FAST!).
    This replaces pixel-by-pixel drawing for entire frame updates.
    
    Args:
        client: BLE client or DualPanelClient
        image: PIL Image to display (RGB mode)
        clear_first: If True, clear screen before uploading
    
    For dual panels:
        - If image is 64x40, it will be split and sent to both panels
        - If image is 64x20, it will be sent to top panel only
    """
    if clear_first:
        await write_cmd(client, CLEAR_SCREEN)
        await asyncio.sleep(0.1)
    
    # Send "stop drawing" command (prepares panel for PNG)
    stop_draw = bytearray([0x05, 0x00, 0x04, 0x01, 0x00])
    
    if isinstance(client, DualPanelClient):
        # Handle dual panel mode
        if image.height == DISPLAY_HEIGHT:
            # Split 64x40 image into top (0-19) and bottom (20-39)
            top_img = image.crop((0, 0, DISPLAY_WIDTH, PANEL_HEIGHT))
            bottom_img = image.crop((0, PANEL_HEIGHT, DISPLAY_WIDTH, DISPLAY_HEIGHT))
            
            # Upload to top panel
            await client.top_client.write_gatt_char(UUID_WRITE_DATA, stop_draw, response=False)
            await asyncio.sleep(0.05)
            top_packet = create_png_packet(top_img)
            await write_cmd_single(client.top_client, top_packet)
            await asyncio.sleep(0.2)
            
            # Upload to bottom panel
            await client.bottom_client.write_gatt_char(UUID_WRITE_DATA, stop_draw, response=False)
            await asyncio.sleep(0.05)
            bottom_packet = create_png_packet(bottom_img)
            await write_cmd_single(client.bottom_client, bottom_packet)
            await asyncio.sleep(0.2)
        else:
            # Single panel size - send to top only
            await client.top_client.write_gatt_char(UUID_WRITE_DATA, stop_draw, response=False)
            await asyncio.sleep(0.05)
            packet = create_png_packet(image)
            await write_cmd_single(client.top_client, packet)
            await asyncio.sleep(0.2)
    else:
        # Single client mode
        await client.write_gatt_char(UUID_WRITE_DATA, stop_draw, response=False)
        await asyncio.sleep(0.05)
        packet = create_png_packet(image)
        await write_cmd_single(client, packet)
        await asyncio.sleep(0.2)


async def write_cmd_single(client, data: bytes):
    """Write command to a single client with chunking (helper for upload_png)"""
    try:
        chunk_size = client.services.get_characteristic(UUID_WRITE_DATA).max_write_without_response_size
    except:
        chunk_size = 512
    
    for i in range(0, len(data), chunk_size):
        await client.write_gatt_char(UUID_WRITE_DATA, data[i:i+chunk_size], response=False)
    await asyncio.sleep(0.01)


# --- Power Control ---
async def led_on(client):
    """Turn the LED display on"""
    print("💡 Turning display ON...")
    await write_cmd(client, SCREEN_ON)
    await asyncio.sleep(0.2)
    print("✅ Display is ON")


async def led_off(client):
    """Turn the LED display off"""
    print("🌙 Turning display OFF...")
    await write_cmd(client, SCREEN_OFF)
    await asyncio.sleep(0.2)
    print("✅ Display is OFF")


