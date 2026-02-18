"""
Clock component for displaying time.
"""

from typing import Optional, Any
from PIL import Image
from .base import Component


class ClockComponent(Component):
    """
    Displays current time with configurable themes.
    
    Config options:
        - theme: Clock theme name (default: "stranger_things")
        - hour24: Use 24-hour format (default: false)
    """
    
    async def fetch_data(self) -> Optional[Any]:
        """Clock doesn't need to fetch data - uses current time."""
        return None
    
    def render(self, data: Optional[Any] = None) -> Image.Image:
        """
        Render clock component.
        
        Args:
            data: Not used (clock uses current time)
        
        Returns:
            PIL Image
        """
        from core.rendering.clock_display_png import render_clock
        
        theme = self.config.get('theme', 'stranger_things')
        hour24 = self.config.get('hour24', False)
        
        return render_clock(
            width=self.width,
            height=self.height,
            theme=theme,
            hour24=hour24
        )


