"""
Base mode class defining the interface for all display modes.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass
from PIL import Image


@dataclass
class ModeResult:
    """Result from a mode's render cycle."""
    image: Optional[Image.Image] = None  # Rendered image, or None if should skip
    should_skip: bool = False  # True if mode has no data to display
    priority: bool = False  # True if this mode should override cycling
    state_changed: bool = False  # True if underlying data changed


class BaseMode(ABC):
    """
    Abstract base class for display modes.
    
    Each mode handles its own:
    - Data fetching and caching
    - Change detection
    - Rendering logic
    - Refresh timing
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize the mode.
        
        Args:
            name: Mode identifier (e.g., "sports", "clock")
            config: Configuration dict with all settings
        """
        self.name = name
        self.config = config
        self.last_render = None
        self.last_fetch = None
        self._state = {}  # Internal state storage
    
    @abstractmethod
    async def fetch_data(self) -> bool:
        """
        Fetch fresh data from external sources.
        
        Returns:
            True if fetch succeeded, False otherwise
        """
        pass
    
    @abstractmethod
    def has_data(self) -> bool:
        """
        Check if mode has data to display.
        
        Returns:
            True if data is available, False if should skip
        """
        pass
    
    @abstractmethod
    def should_fetch(self, now: datetime) -> bool:
        """
        Determine if data needs to be fetched.
        
        Args:
            now: Current datetime
            
        Returns:
            True if fetch is needed
        """
        pass
    
    @abstractmethod
    def should_render(self, now: datetime) -> bool:
        """
        Determine if display should be re-rendered.
        
        Args:
            now: Current datetime
            
        Returns:
            True if render is needed
        """
        pass
    
    @abstractmethod
    async def render(self, width: int, height: int) -> Optional[Image.Image]:
        """
        Render the mode's display.
        
        Args:
            width: Display width in pixels
            height: Display height in pixels
            
        Returns:
            PIL Image or None if nothing to display
        """
        pass
    
    @abstractmethod
    def has_priority(self) -> bool:
        """
        Check if this mode should override normal cycling.
        
        Returns:
            True if mode should take priority (e.g., live sports)
        """
        pass
    
    async def update(self, width: int, height: int, now: datetime) -> ModeResult:
        """
        Main update loop for the mode.
        
        Args:
            width: Display width
            height: Display height
            now: Current datetime
            
        Returns:
            ModeResult with rendering outcome
        """
        # Fetch data if needed
        if self.should_fetch(now):
            await self.fetch_data()
        
        # Check if we have data
        if not self.has_data():
            return ModeResult(should_skip=True)
        
        # Check if we need to render
        if not self.should_render(now):
            return ModeResult()  # No render needed
        
        # Render the display
        image = await self.render(width, height)
        self.last_render = now
        
        return ModeResult(
            image=image,
            priority=self.has_priority(),
            state_changed=True
        )
    
    def reset_state(self):
        """Reset mode state when entering this mode."""
        self._state = {}
        self.last_render = None

