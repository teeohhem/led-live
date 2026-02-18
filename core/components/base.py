"""
Base classes for the component system.

Components are self-contained widgets that:
1. Know how to fetch their own data (optional)
2. Know how to render themselves
3. Can be positioned anywhere on the canvas
4. Can be configured via YAML
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Type
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class Component(ABC):
    """
    Base class for all renderable components.
    
    A component is a self-contained widget that can render itself
    onto a canvas at a specific position.
    
    Examples: Clock, WeatherCurrent, SportsList, StockTicker
    """
    
    def __init__(self, x: int, y: int, width: int, height: int, config: Optional[Dict[str, Any]] = None):
        """
        Initialize component.
        
        Args:
            x: X position on canvas
            y: Y position on canvas
            width: Component width
            height: Component height
            config: Component-specific configuration
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    async def fetch_data(self) -> Optional[Any]:
        """
        Fetch data needed for this component.
        
        Returns:
            Component-specific data, or None if fetch fails
            
        Note:
            Some components (like clock) don't need to fetch data.
            They can return None or empty dict.
        """
        pass
    
    @abstractmethod
    def render(self, data: Optional[Any] = None) -> Image.Image:
        """
        Render component to an image.
        
        Args:
            data: Data returned from fetch_data()
        
        Returns:
            PIL Image of size (self.width, self.height)
        """
        pass
    
    @classmethod
    def from_config(cls, component_config: Dict[str, Any]) -> 'Component':
        """
        Create component instance from config dict.
        
        Args:
            component_config: Config dict with x, y, width, height, config
        
        Returns:
            Component instance
        """
        return cls(
            x=component_config.get('x', 0),
            y=component_config.get('y', 0),
            width=component_config.get('width', 64),
            height=component_config.get('height', 20),
            config=component_config.get('config', {})
        )
    
    def get_bounds(self) -> tuple:
        """Get component bounding box: (x, y, x+width, y+height)"""
        return (self.x, self.y, self.x + self.width, self.y + self.height)
    
    def __repr__(self):
        return f"{self.__class__.__name__}(x={self.x}, y={self.y}, w={self.width}, h={self.height})"


class ComponentRegistry:
    """
    Registry for component types.
    
    Maps component type names (e.g., 'clock', 'weather_current')
    to their implementation classes.
    """
    
    def __init__(self):
        self._components: Dict[str, Type[Component]] = {}
    
    def register(self, type_name: str, component_class: Type[Component]):
        """
        Register a component type.
        
        Args:
            type_name: Type identifier (e.g., 'clock')
            component_class: Component class
        """
        self._components[type_name] = component_class
        logger.info(f"Registered component: {type_name} -> {component_class.__name__}")
    
    def create(self, type_name: str, component_config: Dict[str, Any]) -> Optional[Component]:
        """
        Create a component instance from config.
        
        Args:
            type_name: Component type (e.g., 'clock')
            component_config: Component configuration
        
        Returns:
            Component instance, or None if type not found
        """
        component_class = self._components.get(type_name)
        
        if not component_class:
            logger.error(f"Unknown component type: {type_name}")
            return None
        
        try:
            return component_class.from_config(component_config)
        except Exception as e:
            logger.error(f"Failed to create {type_name} component: {e}")
            return None
    
    def list_types(self) -> list:
        """Get list of registered component types."""
        return list(self._components.keys())
    
    def get_class(self, type_name: str) -> Optional[Type[Component]]:
        """Get component class for a type."""
        return self._components.get(type_name)


