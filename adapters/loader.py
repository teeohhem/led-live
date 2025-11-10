"""
Adapter loader for dynamically loading display adapters.

This module provides functionality to load and instantiate display adapters
from the adapters registry, allowing users to easily switch between different
display protocols.
"""
import importlib
import json
from pathlib import Path
from typing import Dict, Any, Optional, Type

from .base import DisplayAdapter


class AdapterRegistry:
    """Registry for managing available display adapters."""

    def __init__(self, registry_path: Optional[Path] = None):
        """
        Initialize the adapter registry.

        Args:
            registry_path: Path to adapters.json file. If None, uses default location.
        """
        if registry_path is None:
            registry_path = Path("./adapters.json")

        self.registry_path = registry_path
        self._registry: Optional[Dict[str, Any]] = None

    def load_registry(self) -> Dict[str, Any]:
        """Load the adapter registry from JSON file."""
        if self._registry is None:
            try:
                with open(self.registry_path, 'r') as f:
                    self._registry = json.load(f)
            except FileNotFoundError:
                raise FileNotFoundError(f"Adapter registry not found: {self.registry_path}")
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid adapter registry JSON: {e}")

        return self._registry

    def get_adapter_info(self, adapter_name: str) -> Dict[str, Any]:
        """
        Get information about a specific adapter.

        Args:
            adapter_name: Name of the adapter (key in registry)

        Returns:
            Dictionary with adapter information

        Raises:
            KeyError: If adapter not found in registry
        """
        registry = self.load_registry()
        adapters = registry.get('adapters', {})

        if adapter_name not in adapters:
            available = list(adapters.keys())
            raise KeyError(f"Adapter '{adapter_name}' not found. Available adapters: {available}")

        return adapters[adapter_name]

    def get_default_adapter_name(self) -> Optional[str]:
        """Get the name of the default adapter."""
        registry = self.load_registry()
        adapters = registry.get('adapters', {})

        for name, info in adapters.items():
            if info.get('default', False):
                return name

        # If no default marked, return the first one
        return next(iter(adapters.keys()), None)

    def list_adapters(self) -> Dict[str, Dict[str, Any]]:
        """List all available adapters."""
        registry = self.load_registry()
        return registry.get('adapters', {})

    def create_adapter(self, adapter_name: Optional[str] = None) -> DisplayAdapter:
        """
        Create and return an instance of the specified adapter.

        Args:
            adapter_name: Name of adapter to create. If None, uses default adapter.

        Returns:
            DisplayAdapter instance

        Raises:
            KeyError: If adapter not found
            ImportError: If adapter module/class cannot be imported
            TypeError: If imported class is not a DisplayAdapter
        """
        if adapter_name is None:
            adapter_name = self.get_default_adapter_name()
            if adapter_name is None:
                raise RuntimeError("No adapters available in registry")

        info = self.get_adapter_info(adapter_name)

        # Import the module
        module_name = info['module']
        class_name = info['class']

        try:
            module = importlib.import_module(module_name)
        except ImportError as e:
            raise ImportError(f"Cannot import adapter module '{module_name}': {e}")

        # Get the class
        try:
            adapter_class = getattr(module, class_name)
        except AttributeError:
            raise ImportError(f"Cannot find adapter class '{class_name}' in module '{module_name}'")

        # Verify it's a DisplayAdapter
        if not issubclass(adapter_class, DisplayAdapter):
            raise TypeError(f"Adapter class '{class_name}' is not a DisplayAdapter subclass")

        # Create and return instance
        return adapter_class()


# Global registry instance
_registry = AdapterRegistry()

def get_adapter(adapter_name: Optional[str] = None) -> DisplayAdapter:
    """
    Convenience function to get an adapter instance.

    Args:
        adapter_name: Name of adapter to create. If None, uses default.

    Returns:
        DisplayAdapter instance
    """
    return _registry.create_adapter(adapter_name)

def list_available_adapters() -> Dict[str, Dict[str, Any]]:
    """List all available adapters with their information."""
    return _registry.list_adapters()

def get_default_adapter_name() -> Optional[str]:
    """Get the name of the default adapter."""
    return _registry.get_default_adapter_name()
