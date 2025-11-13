"""
Scrolling ticker rendering for LED panels.

Creates animated frames for scrolling text displays.
"""
from PIL import Image, ImageDraw, ImageFont
from typing import List, Tuple
import asyncio
import logging

logger = logging.getLogger(__name__)


def create_ticker_frames(
    text: str,
    width: int = 64,
    height: int = 10,
    font_path: str = "./fonts/PixelOperator.ttf",
    font_size: int = 8,
    text_color: Tuple[int, int, int] = (255, 255, 255),
    bg_color: Tuple[int, int, int] = (0, 0, 0),
    scroll_speed: int = 2,
    padding: int = 10
) -> List[Image.Image]:
    """
    Create frames for scrolling ticker animation.
    
    Args:
        text: Text to scroll
        width: Display width in pixels
        height: Display height (ticker height)
        font_path: Path to font file
        font_size: Font size
        text_color: RGB color for text
        bg_color: RGB background color
        scroll_speed: Pixels to scroll per frame
        padding: Extra space after text before it loops
    
    Returns:
        List of PIL Images (frames for animation)
    """
    # Load font
    try:
        font = ImageFont.truetype(font_path, font_size)
    except:
        font = ImageFont.load_default()
        logger.warning(f"Could not load font {font_path}, using default")
    
    # Measure text width
    temp_img = Image.new('RGB', (1, 1))
    temp_draw = ImageDraw.Draw(temp_img)
    text_bbox = temp_draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    # Create a long canvas with text + padding
    canvas_width = text_width + padding + width
    canvas = Image.new('RGB', (canvas_width, height), color=bg_color)
    draw = ImageDraw.Draw(canvas)
    
    # Draw text starting off-screen to the right
    text_y = (height - text_height) // 2  # Center vertically
    draw.text((width, text_y), text, fill=text_color, font=font)
    
    # Generate frames by sliding a window across the canvas
    frames = []
    for x_offset in range(0, text_width + padding, scroll_speed):
        # Extract the visible portion
        frame = canvas.crop((x_offset, 0, x_offset + width, height))
        frames.append(frame)
    
    logger.info(f"Created {len(frames)} ticker frames ({text_width}px text, {scroll_speed}px/frame)")
    return frames


def create_multi_line_ticker_frames(
    lines: List[Tuple[str, Tuple[int, int, int]]],
    width: int = 64,
    height: int = 40,
    font_path: str = "./fonts/PixelOperator.ttf",
    font_size: int = 8,
    bg_color: Tuple[int, int, int] = (0, 0, 0),
    scroll_speed: int = 2,
    line_spacing: int = 2
) -> List[Image.Image]:
    """
    Create frames for multi-line scrolling ticker.
    
    Each line can have its own color and scrolls independently.
    
    Args:
        lines: List of (text, color) tuples for each line
        width: Display width
        height: Total display height
        font_path: Font file path
        font_size: Font size
        bg_color: Background color
        scroll_speed: Pixels per frame
        line_spacing: Spacing between lines
    
    Returns:
        List of PIL Images (animation frames)
    """
    # Calculate height per line
    num_lines = len(lines)
    line_height = (height - (line_spacing * (num_lines - 1))) // num_lines
    
    # Create frames for each line
    all_line_frames = []
    max_frames = 0
    
    for text, color in lines:
        line_frames = create_ticker_frames(
            text=text,
            width=width,
            height=line_height,
            font_path=font_path,
            font_size=font_size,
            text_color=color,
            bg_color=bg_color,
            scroll_speed=scroll_speed
        )
        all_line_frames.append(line_frames)
        max_frames = max(max_frames, len(line_frames))
    
    # Composite frames together
    composite_frames = []
    for frame_idx in range(max_frames):
        composite = Image.new('RGB', (width, height), color=bg_color)
        
        y_offset = 0
        for line_idx, line_frames in enumerate(all_line_frames):
            # Loop frames if this line has fewer frames than others
            frame = line_frames[frame_idx % len(line_frames)]
            composite.paste(frame, (0, y_offset))
            y_offset += line_height + line_spacing
        
        composite_frames.append(composite)
    
    logger.info(f"Created {len(composite_frames)} multi-line ticker frames ({num_lines} lines)")
    return composite_frames


async def play_ticker(adapter, text: str, duration: int = 10, **kwargs):
    """
    Play a scrolling ticker on the display.
    
    Args:
        adapter: Display adapter instance
        text: Text to scroll
        duration: How long to play the ticker (seconds)
        **kwargs: Additional arguments for create_ticker_frames
                  (e.g., font_size, text_color, scroll_speed, etc.)
                  Note: width and height are auto-set from adapter unless overridden
    """
    # Set default width/height from adapter if not provided
    if 'width' not in kwargs:
        kwargs['width'] = adapter.display_width
    if 'height' not in kwargs:
        kwargs['height'] = adapter.display_height
    
    # Create frames
    frames = create_ticker_frames(text=text, **kwargs)
    
    if not frames:
        logger.warning("No ticker frames created")
        return
    
    # Use a fixed frame rate for smooth scrolling
    # Instead of spreading frames across duration, use consistent timing
    frame_rate = 30  # Target 30 FPS for smooth scrolling
    frame_delay = 1.0 / frame_rate  # ~0.033s per frame
    
    # Calculate actual duration based on frame count
    actual_duration = len(frames) * frame_delay
    
    logger.info(f"Playing ticker: {len(frames)} frames @ {frame_rate} FPS = {actual_duration:.1f}s")
    
    # Play frames at consistent rate
    from adapters.ipixel.protocol import upload_png
    
    for frame in frames:
        await upload_png(adapter.client, frame, clear_first=False)
        await asyncio.sleep(frame_delay)
    
    logger.info("Ticker playback complete")

