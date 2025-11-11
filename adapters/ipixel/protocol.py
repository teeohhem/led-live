"""
BLE protocol implementation for iPixel LED panels.

This module contains the low-level BLE communication protocol for iPixel LED panels,
including PNG packet creation, command formatting, and BLE-specific constants.

Panel dimensions are set by the adapter via set_panel_dimensions() at initialization.
Panel count is determined by the number of BLE addresses in config.yml.
"""
import asyncio
import binascii
import io
import os
import time
import zlib
from pathlib import Path
from typing import Optional, Tuple
import logging
logger = logging.getLogger(__name__)

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# --- Utility functions for packet creation ---

def switch_endian(hex_string):
    """Switch endianness of hex string (pairs of characters)."""
    if len(hex_string) % 2 != 0:
        raise ValueError("The length of the hexadecimal string must be even.")
    # Split into pairs, reverse, and join
    pairs = [hex_string[i:i+2] for i in range(0, len(hex_string), 2)]
    return ''.join(reversed(pairs))

def CRC32_checksum(data):
    """Calculate CRC32 checksum of hex data (with endian switch)."""
    try:
        calculated_crc = binascii.crc32(bytes.fromhex(data)) & 0xFFFFFFFF
        calculated_crc_hex = f"{calculated_crc:08x}"
        # Send the checksum by switching endian (like )
        return switch_endian(calculated_crc_hex)
    except ValueError as e:
        logger.error(f"CRC32error:Invalidhexdata'{data[:50]}...'-{e}")
        raise

def get_frame_size(data, size):
    """Get frame size in hex format."""
    return switch_endian(hex(len(data) // 2)[2:].zfill(size))

# Display dimensions - MUST be set by adapter via set_panel_dimensions()
# Initialized to None to force explicit configuration
PANEL_WIDTH = None
PANEL_HEIGHT = None

def set_panel_dimensions(width: int, height: int):
    """
    Set panel dimensions (called by adapter at initialization).
    MUST be called before any image operations.
    
    Args:
        width: Panel width in pixels (e.g., 64)
        height: Panel height in pixels (e.g., 20)
        
    Raises:
        ValueError: If width or height are invalid
    """
    global PANEL_WIDTH, PANEL_HEIGHT
    
    if not isinstance(width, int) or width <= 0:
        raise ValueError(f"Panel width must be a positive integer, got {width}")
    if not isinstance(height, int) or height <= 0:
        raise ValueError(f"Panel height must be a positive integer, got {height}")
    
    PANEL_WIDTH = width
    PANEL_HEIGHT = height
    logger.info(f"📐Protocoldimensionssetto{PANEL_WIDTH}x{PANEL_HEIGHT}")

def _check_dimensions():
    """Check that dimensions have been set. Call this before using PANEL_WIDTH/HEIGHT."""
    if PANEL_WIDTH is None or PANEL_HEIGHT is None:
        raise RuntimeError(
            "Panel dimensions not set! Adapter must call set_panel_dimensions() at initialization. "
            "This is typically done in BLEDisplayAdapter._load_panel_dimensions()"
        )

# --- BLE / Panel settings ---
def _get_uuid_write():
    """Get BLE write characteristic UUID from config or use default."""
    try:
        from config_loader import get_config, load_config
        try:
            config = get_config()
        except RuntimeError:
            # Config not initialized yet, load it
            config = load_config()
        return config.get_string("display.ipixel.ble_uuid_write", 
                                "0000fa02-0000-1000-8000-00805f9b34fb")
    except Exception:
        return "0000fa02-0000-1000-8000-00805f9b34fb"

UUID_WRITE_DATA = _get_uuid_write()

# Panel count is derived from number of BLE addresses (see _get_panel_addresses())
# PANEL_COUNT will be calculated dynamically based on BLE_ADDRESSES
# DISPLAY_HEIGHT will be PANEL_HEIGHT * panel_count

# Panel BLE addresses (from centralized config module)
def _get_panel_addresses():
    """
    Get list of BLE addresses for configured panels.
    
    The number of addresses determines the panel count automatically.
    Loaded from config.py which reads config.yml at startup.
    
    Returns:
        list: BLE addresses in order, one for each panel
        
    Raises:
        ValueError: If BLE_ADDRESSES not configured
    """
    try:
        # Import from centralized config module
        from config import IPIXEL_BLE_ADDRESSES
        ble_addresses = IPIXEL_BLE_ADDRESSES
    except ImportError as e:
        raise ValueError(f"Failed to import config: {e}")
    
    if not ble_addresses or not all(isinstance(addr, str) for addr in ble_addresses):
        raise ValueError(
            "BLE_ADDRESSES not configured in config.yml. "
            "Set display.ipixel.ble_addresses to a list of panel BLE addresses. "
            "See config.yml.example for the format."
        )
    
    return ble_addresses

# --- BLE Commands ---
SCREEN_ON = bytearray([5, 0, 7, 1, 1])
SCREEN_OFF = bytearray([5, 0, 7, 1, 0])
CLEAR_SCREEN = bytearray([5, 0, 8, 1, 1])


# --- BLE write helper ---
async def write_cmd(client, data: bytes):
    """
    Write command to client with proper chunking (like idotmatrix library does).
    Chunks data based on MTU size for reliable transmission.

    Args:
        client: BLE client or MultiPanelClient
        data: Command data to send
    """
    if isinstance(client, MultiPanelClient):
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


# --- Internal helpers for GIF (re)size ---

def _resolve_target_size(width, height) -> Optional[Tuple[int, int]]:
    """Return (w, h) as ints if provided or available from config, else None."""
    _check_dimensions()  # Ensure dimensions are set
    
    if width is not None and height is not None:
        try:
            return int(width), int(height)
        except (TypeError, ValueError):
            raise ValueError("width and height must be integers")
    # For GIF animations, target individual panel size (PANEL_WIDTH x PANEL_HEIGHT)
    return (PANEL_WIDTH, PANEL_HEIGHT)


def _resize_image_if_needed(img, target_size: Optional[Tuple[int, int]]):
    if not PIL_AVAILABLE:
        raise ImportError("PIL (Pillow) is required for image processing")

    if target_size and img.size != target_size:
        return img.resize(target_size, Image.Resampling.LANCZOS)
    return img


def _gif_bytes(data: bytes, target_size: Optional[Tuple[int, int]], max_frames: int) -> bytes:
    """Process GIF data with optional resizing and frame limiting."""
    if not PIL_AVAILABLE:
        raise ImportError("PIL (Pillow) is required for GIF animation support")

    try:
        gif_buffer = io.BytesIO(data)
        with Image.open(gif_buffer) as img:
            logger.info(f"GIFinfo:{img.size},{getattr(img,'n_frames',1)}frames,duration={img.info.get('duration','N/A')}")

            duration = img.info.get("duration", 500)
            loop = img.info.get("loop", 0)

            if getattr(img, "n_frames", 1) > 1:
                frame_count = min(max(1, int(max_frames)), img.n_frames)
                logger.info(f"🎬Processing{frame_count}frames...")
                frames = []
                for idx in range(frame_count):
                    img.seek(idx)
                    frame = _resize_image_if_needed(img.copy(), target_size)
                    frames.append(frame.convert("P"))

                output_buffer = io.BytesIO()
                frames[0].save(
                    output_buffer,
                    format="GIF",
                    save_all=True,
                    append_images=frames[1:],
                    duration=duration,
                    loop=loop,
                    optimize=False  # Don't optimize to preserve frames
                )
                result = output_buffer.getvalue()
                logger.info(f"📦Createdmulti-frameGIF:{len(result)}bytes")
                return result

            # Single-frame GIF
            logger.info("📸Processingsingle-frameGIF...")
            img = _resize_image_if_needed(img, target_size)
            output_buffer = io.BytesIO()
            img.save(output_buffer, format="GIF", loop=loop, duration=duration)
            result = output_buffer.getvalue()
            logger.info(f"📦Createdsingle-frameGIF:{len(result)}bytes")
            return result

    except Exception as e:
        logger.error(f"ErrorprocessingGIF:{e}")
        import traceback
        traceback.print_exc()
        raise


# --- Panel targeting helper ---
def _normalize_panel_indices(panels, total_panels):
    """
    Convert panel specification to list of panel indices (0-based).
    
    Args:
        panels: List of panel indices (0-based). Empty list means all panels.
                Example: [] or None = all panels, [0] = panel 0, [0, 2] = panels 0 and 2
            
        total_panels: Total number of panels available
        
    Returns:
        list: List of panel indices to target
        
    Raises:
        ValueError: If panels argument is invalid
    """
    # Empty list or None means all panels
    if panels is None or (isinstance(panels, list) and len(panels) == 0):
        return list(range(total_panels))
    
    # Must be a list
    if not isinstance(panels, list):
        raise ValueError(f"panels must be a list of indices, got {type(panels)}")
    
    # Validate all indices
    for p in panels:
        if not isinstance(p, int):
            raise ValueError(f"Panel indices must be integers, got {type(p)}")
        if p < 0 or p >= total_panels:
            raise ValueError(f"Panel index {p} out of range (0-{total_panels-1})")
    
    return panels


# --- GIF Animation Upload ---
def create_gif_packet(gif_data, max_frames=None):
    """
    Convert GIF data to panel upload packet (animation format).

    Args:
        gif_data: Bytes of GIF file data
        max_frames: Maximum number of frames to include (optional)

    Returns:
        bytes: Complete packet ready to send
    """
    # Process GIF with resizing to panel dimensions
    target_size = _resolve_target_size(None, None)
    frame_limit = max_frames if max_frames else 100

    processed_gif_data = _gif_bytes(gif_data, target_size, frame_limit)
    if len(processed_gif_data) == 0:
        raise ValueError("GIF processing produced empty data")

    gif_hex = processed_gif_data.hex()

    # Validate hex format
    if not all(c in '0123456789abcdefABCDEF' for c in gif_hex):
        raise ValueError(f"GIF hex contains invalid characters")

    # Calculate CRC32 checksum
    checksum = CRC32_checksum(gif_hex)

    # Get size in hex (little endian format)
    size = get_frame_size(gif_hex, 8)

    # Build the packet exactly like  send_animation
    prefix = "FFFF030000" + size + checksum + "0201" + gif_hex
    frame_size = get_frame_size(prefix, 4)

    packet_hex = f"{frame_size}030000{size}{checksum}0201{gif_hex}"

    # Validate final packet hex
    if len(packet_hex) % 2 != 0:
        raise ValueError(f"Packet hex length must be even")
    if not all(c in '0123456789abcdefABCDEF' for c in packet_hex):
        raise ValueError(f"Packet hex contains invalid characters")

    return bytes.fromhex(packet_hex)


async def upload_gif(client, gif_path_or_data, clear_first=False, max_frames=None, panels=None):
    """
    Upload a GIF animation to panel(s).
    Supports multi-frame animated GIFs with automatic resizing to panel dimensions.

    Args:
        client: BLE client or MultiPanelClient
        gif_path_or_data: Path to GIF file or bytes data
        clear_first: If True, clear screen before uploading
        max_frames: Maximum number of frames to include (None = all frames)
        panels: List of panel indices (0-based) to target. 
                Empty list [] or None = all panels.
                Example: [0] = panel 0, [0, 2] = panels 0 and 2
    """
    _check_dimensions()  # Ensure dimensions are set
    
    if clear_first:
        await write_cmd(client, CLEAR_SCREEN)
        await asyncio.sleep(0.1)

    await play_gif_frames(client, gif_path_or_data, loop=False, max_frames=max_frames, panels=panels)


async def play_gif_frames(client, gif_path_or_data, loop=True, max_frames=None, panels=None):
    """
    Play GIF animation by displaying frames one by one with proper timing.
    Each frame is uploaded as a PNG for reliable display.

    Args:
        client: BLE client or MultiPanelClient
        gif_path_or_data: Path to GIF file or bytes data
        loop: If True, loop the animation indefinitely
        max_frames: Maximum number of frames to display (None = all frames)
        panels: List of panel indices (0-based) to target.
                Empty list [] or None = all panels.
                Example: [0] = panel 0, [0, 2] = panels 0 and 2
    """
    _check_dimensions()  # Ensure dimensions are set
    
    if not PIL_AVAILABLE:
        raise ImportError("PIL (Pillow) is required for GIF animation support")

    # Load GIF data
    if isinstance(gif_path_or_data, str) and os.path.isfile(gif_path_or_data):
        with open(gif_path_or_data, 'rb') as f:
            gif_data = f.read()
    elif isinstance(gif_path_or_data, bytes):
        gif_data = gif_path_or_data
    else:
        raise ValueError("gif_path_or_data must be a file path or bytes")

    # Process GIF and extract frames
    gif_buffer = io.BytesIO(gif_data)
    with Image.open(gif_buffer) as img:
        total_frames = getattr(img, "n_frames", 1)
        frame_count = min(max_frames or total_frames, total_frames)

        while True:
            for frame_idx in range(frame_count):
                img.seek(frame_idx)

                # Get frame timing (default 100ms if not specified)
                duration = img.info.get("duration", 100) / 1000.0

                # Convert frame to RGB and resize if needed
                frame_rgb = img.convert("RGB")
                target_size = _resolve_target_size(None, None)
                if frame_rgb.size != target_size:
                    frame_rgb = frame_rgb.resize(target_size, Image.Resampling.LANCZOS)

                # Upload frame as PNG
                await upload_png(client, frame_rgb, clear_first=False, panels=panels)

                # Wait for frame duration
                await asyncio.sleep(duration)

            if not loop:
                break


def _parse_gif_transport(data: bytes):
    """Parse GIF transport payload (same as )."""
    if len(data) < 2 + 13:
        return None
    offset = 2  # skip 2-byte length prefix
    if data[offset] != 0x03 or data[offset + 1] != 0x00:
        return None
    option_byte = data[offset + 2]
    size_bytes = data[offset + 3: offset + 7]
    crc_bytes = data[offset + 7: offset + 11]
    if data[offset + 11] != 0x02 or data[offset + 12] != 0x01:
        return None
    tail_bytes = data[offset + 11: offset + 13]
    gif_len = int.from_bytes(size_bytes, "little")
    gif_start = offset + 13
    if gif_start + gif_len > len(data):
        return None
    gif_bytes = data[gif_start: gif_start + gif_len]

    return {
        "gif_bytes": gif_bytes,
        "size_bytes": size_bytes,
        "crc_bytes": crc_bytes,
        "tail_bytes": tail_bytes
    }


async def _send_gif_windowed(client, data: bytes, chunk_size: int = 244, window_size: int = 12 * 1024):
    """Send GIF data using windowed approach (same as )."""
    parsed = _parse_gif_transport(data)
    if not parsed:
        # Fall back to regular chunked sending
        await write_cmd(client, data)
        return

    gif = parsed["gif_bytes"]
    size_bytes = parsed["size_bytes"]
    crc_bytes = parsed["crc_bytes"]

    pos = 0
    window_index = 0
    while pos < len(gif):
        window_end = min(pos + window_size, len(gif))
        chunk_payload = gif[pos:window_end]

        # Different headers for first vs subsequent chunks
        option = 0x00 if window_index == 0 else 0x02
        serial = 0x01 if window_index == 0 else 0x65

        cur_tail = bytes([0x02, serial])
        header = bytes([0x03, 0x00, option]) + size_bytes + crc_bytes + cur_tail
        frame = header + chunk_payload

        # Calculate prefix using the same method as 
        prefix_hex = get_frame_size("FFFF" + frame.hex(), 4)
        try:
            prefix = bytes.fromhex(prefix_hex)
        except Exception:
            # Fallback: 2-byte big-endian length prefix = (frame_len + 2)
            total = len(frame) + 2
            prefix = total.to_bytes(2, "big")
        
        message = prefix + frame

        # Send this chunk in smaller pieces (chunk_size)
        wpos = 0
        while wpos < len(message):
            wend = min(wpos + chunk_size, len(message))
            await write_cmd(client, message[wpos:wend])
            await asyncio.sleep(0.01)
            wpos = wend

        pos = window_end
        window_index += 1


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
    # Ensure image is in RGB mode
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Convert image to PNG in memory
    png_buffer = io.BytesIO()
    image.save(png_buffer, format='PNG', optimize=False)
    png_data = png_buffer.getvalue()

    # Calculate CRC32 of PNG data
    crc = zlib.crc32(png_data) & 0xFFFFFFFF

    # Build packet header (15 bytes)
    png_len = len(png_data)
    total_len = png_len + 15  # PNG data + 15-byte header
    logger.info(f"CreatingPNGpacket:image{image.width}x{image.height},PNG{png_len}bytes,CRC{crc:08x}")

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


async def upload_png(client, image, clear_first=False, panels=None):
    """
    Upload a PIL Image to panel(s) using PNG upload (FAST!).
    This replaces pixel-by-pixel drawing for entire frame updates.

    Args:
        client: BLE client or MultiPanelClient
        image: PIL Image to display (RGB mode)
        clear_first: If True, clear screen before uploading
        panels: List of panel indices (0-based) to target.
                Empty list [] or None = all panels (default).
                Example: [0] = panel 0, [0, 2] = panels 0 and 2

    For multi-panels:
        - If image height matches total display height, it will be split across panels
        - If image height matches single panel height, it will be sent to specified panel(s)
    """
    _check_dimensions()  # Ensure dimensions are set
    
    logger.debug(f"upload_pngcalled:imagesize{image.width}x{image.height},panels={panels}")
    
    if clear_first:
        await write_cmd(client, CLEAR_SCREEN)
        await asyncio.sleep(0.1)

    # Send "stop drawing" command (prepares panel for PNG)
    stop_draw = bytearray([0x05, 0x00, 0x04, 0x01, 0x00])

    # Normalize panel indices
    target_panels = _normalize_panel_indices(panels, client.panel_count)
    logger.info(f"Targetpanels:{target_panels},totalpanels:{client.panel_count}")

    # Calculate total display dimensions
    total_display_height = PANEL_HEIGHT * client.panel_count
    
    # If image height matches full display, split it across panels
    if image.height == total_display_height and len(target_panels) > 1:
        # Split image: each panel gets PANEL_HEIGHT pixels
        for panel_idx in target_panels:
            y_start = panel_idx * PANEL_HEIGHT
            y_end = y_start + PANEL_HEIGHT
            
            # Crop image for this panel
            panel_img = image.crop((0, y_start, PANEL_WIDTH, y_end))
            
            # Send to this panel
            panel_client = client.get_panel_client(panel_idx)
            logger.info(f"Sendingtopanel{panel_idx}...")
            await panel_client.write_gatt_char(UUID_WRITE_DATA, stop_draw, response=False)
            await asyncio.sleep(0.05)
            packet = create_png_packet(panel_img)
            logger.info(f"PNGpacketcreated:{len(packet)}bytes")
            await write_cmd_single(panel_client, packet)
            logger.info(f"Senttopanel{panel_idx}")
            await asyncio.sleep(0.2)
    else:
        # Single panel image or single target panel
        # Send same image to all target panels
        logger.info(f"Singleimagemode-sendingto{len(target_panels)}panel(s)")
        for panel_idx in target_panels:
            panel_client = client.get_panel_client(panel_idx)
            logger.info(f"Sendingtopanel{panel_idx}...")
            await panel_client.write_gatt_char(UUID_WRITE_DATA, stop_draw, response=False)
            await asyncio.sleep(0.05)
            packet = create_png_packet(image)
            logger.info(f"PNGpacketcreated:{len(packet)}bytes")
            await write_cmd_single(panel_client, packet)
            logger.info(f"Senttopanel{panel_idx}")
            await asyncio.sleep(0.2)


async def write_cmd_single(client, data: bytes):
    """Write command to a single client with chunking (helper for upload_png)"""
    try:
        chunk_size = client.services.get_characteristic(UUID_WRITE_DATA).max_write_without_response_size
    except Exception as e:
        logger.warning(f"Couldnotgetchunksize:{e},usingdefault512")
        chunk_size = 512

    total_sent = 0
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i+chunk_size]
        try:
            await client.write_gatt_char(UUID_WRITE_DATA, chunk, response=False)
            total_sent += len(chunk)
        except Exception as e:
            logger.error(f"BLEwriteerror:{e}")
            raise
    
    logger.info(f"Sent{total_sent}bytesin{(total_sent+chunk_size-1)//chunk_size}chunks")
    await asyncio.sleep(0.01)


# --- Screen management ---
async def clear_screen_completely(client):
    """Clear the screen by sending clear command (dual-panel compatible)"""
    logger.info("Clearingpanels...")
    try:
        await write_cmd(client, CLEAR_SCREEN)
        await asyncio.sleep(0.3)
        logger.info("Panelscleared")
    except Exception as e:
        logger.error(f"Clearfailed:{e}")


async def init_panels(client):
    """Initialize panels after connection"""
    logger.info("Bothpanelsconnected,initializing...")
    await write_cmd(client, SCREEN_ON)
    await asyncio.sleep(0.2)
    logger.info("Bothpanelsinitialized")


# --- Power Control ---
async def led_on(client):
    """Turn the LED display on"""
    logger.debug("TurningdisplayON...")
    await write_cmd(client, SCREEN_ON)
    await asyncio.sleep(0.2)
    logger.info("DisplayisON")


async def led_off(client):
    """Turn the LED display off"""
    logger.info("🌙TurningdisplayOFF...")
    await write_cmd(client, SCREEN_OFF)
    await asyncio.sleep(0.2)
    logger.info("DisplayisOFF")


# --- Multi Panel Client Wrapper ---
class MultiPanelClient:
    """
    Wrapper for multi-panel setup supporting 1, 2, 3, or more panels.
    Routes commands to the correct panel(s) based on configuration.
    """
    def __init__(self, panel_clients):
        """
        Initialize with a list of BLE clients for each panel.
        
        Args:
            panel_clients: List of BLE clients (1 or more), indexed by panel position
        """
        if not panel_clients:
            raise ValueError("Must provide at least one panel client")
        
        self.panel_clients = panel_clients
        self.panel_count = len(panel_clients)
        
        # Legacy access for backward compatibility (if using 2 panels)
        if self.panel_count >= 1:
            self.top_client = panel_clients[0]
        if self.panel_count >= 2:
            self.bottom_client = panel_clients[1]

    async def write_gatt_char(self, uuid, data, response=False):
        """Write to all panels"""
        for client in self.panel_clients:
            await client.write_gatt_char(uuid, data, response=response)

    async def connect(self):
        """All panels should already be connected"""
        pass

    async def disconnect(self):
        """Disconnect all panels"""
        for client in self.panel_clients:
            await client.disconnect()

    def get_panel_client(self, panel_index: int):
        """Get a specific panel's client by index."""
        if panel_index < 0 or panel_index >= self.panel_count:
            raise IndexError(f"Panel index {panel_index} out of range (0-{self.panel_count-1})")
        return self.panel_clients[panel_index]
