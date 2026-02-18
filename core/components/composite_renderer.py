"""
Composite renderer that combines multiple components into a single display.
"""

from typing import List, Dict, Any
from PIL import Image
import asyncio
import logging

from .base import Component, ComponentRegistry

logger = logging.getLogger(__name__)


class CompositeRenderer:
    """
    Renders a canvas with multiple positioned components.
    
    Takes a template definition with component list and renders
    them all onto a single canvas.
    """
    
    def __init__(self, template_config: Dict[str, Any], registry: ComponentRegistry):
        """
        Initialize composite renderer.
        
        Args:
            template_config: Template configuration dict
            registry: Component registry for creating components
        """
        self.template_name = template_config.get('name', 'untitled')
        self.canvas_width = template_config.get('canvas_width', 64)
        self.canvas_height = template_config.get('canvas_height', 40)
        self.background_color = tuple(template_config.get('background_color', [0, 0, 0]))
        
        # Create component instances
        self.components: List[Component] = []
        for comp_config in template_config.get('components', []):
            comp_type = comp_config.get('type')
            if not comp_type:
                logger.warning("Component missing 'type' field")
                continue
            
            component = registry.create(comp_type, comp_config)
            if component:
                self.components.append(component)
                logger.info(f"Added {comp_type} component: {component}")
            else:
                logger.error(f"Failed to create component: {comp_type}")
    
    async def fetch_all_data(self) -> Dict[int, Any]:
        """
        Fetch data for all components in parallel.
        
        Returns:
            Dict mapping component index to its data
        """
        # Fetch all component data concurrently
        tasks = [comp.fetch_data() for comp in self.components]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Map component index to data
        data_map = {}
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Component {idx} fetch failed: {result}")
                data_map[idx] = None
            else:
                data_map[idx] = result
        
        return data_map
    
    async def render(self, force_refresh: bool = False) -> Image.Image:
        """
        Render complete canvas with all components.
        
        Args:
            force_refresh: Force re-fetch of all data
        
        Returns:
            PIL Image of full canvas
        """
        # Create canvas
        canvas = Image.new('RGB', (self.canvas_width, self.canvas_height), self.background_color)
        
        # Fetch all data
        if force_refresh:
            logger.info("Force refreshing all component data")
        
        data_map = await self.fetch_all_data()
        
        # Render each component
        for idx, component in enumerate(self.components):
            try:
                component_data = data_map.get(idx)
                component_img = component.render(component_data)
                
                # Paste onto canvas at component position
                if component_img:
                    canvas.paste(component_img, (component.x, component.y))
                    logger.debug(f"Rendered {component} at ({component.x}, {component.y})")
                else:
                    logger.warning(f"Component {idx} returned no image")
            
            except Exception as e:
                logger.error(f"Failed to render component {idx} ({component}): {e}")
                # Continue with other components
        
        return canvas
    
    def get_component_count(self) -> int:
        """Get number of components in this template."""
        return len(self.components)
    
    def __repr__(self):
        return f"CompositeRenderer('{self.template_name}', {self.canvas_width}x{self.canvas_height}, {len(self.components)} components)"


def load_composite_template(template_path: str, registry: ComponentRegistry) -> CompositeRenderer:
    """
    Load a composite template from YAML file.
    
    Args:
        template_path: Path to YAML template file
        registry: Component registry
    
    Returns:
        CompositeRenderer instance
    """
    import yaml
    
    with open(template_path, 'r') as f:
        template_config = yaml.safe_load(f)
    
    return CompositeRenderer(template_config, registry)


