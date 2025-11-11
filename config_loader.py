"""
Configuration loader for LED Panel Display System.

Supports YAML configuration files with environment variable overrides.
Loads config.yml by default, falls back to environment variables.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger('led_panel.config_loader')

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


class ConfigLoader:
    """Load configuration from YAML file or environment variables."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize config loader.
        
        Args:
            config_path: Path to config.yml file. If None, tries default location.
        """
        if config_path is None:
            # Try multiple locations in order of preference
            candidates = [
                Path.cwd() / "config.yml",                         # Current working directory
                Path(__file__).parent / "config.yml",              # Same directory as this file (project root)
                Path.home() / ".led_panel" / "config.yml",         # User home
            ]
            
            config_path = None
            for candidate in candidates:
                # Use absolute path to avoid ambiguity
                abs_candidate = candidate.resolve() if candidate.is_absolute() else candidate
                if abs_candidate.exists():
                    config_path = abs_candidate
                    break
            
            # If no file found, prefer project root location (will show error later)
            if config_path is None:
                config_path = (Path(__file__).parent / "config.yml").resolve()
        
        self.config_path = config_path
        self._config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from YAML file."""
        # Ensure we have an absolute path
        config_path = self.config_path.resolve() if not self.config_path.is_absolute() else self.config_path
        
        if config_path.exists() and YAML_AVAILABLE:
            try:
                with open(config_path, 'r') as f:
                    self._config = yaml.safe_load(f) or {}
                logger.info(f"Loaded configuration from {config_path}")
            except yaml.YAMLError as e:
                logger.error(f"Error parsing {config_path}: {e}")
        elif not YAML_AVAILABLE:
            logger.error("PyYAML not installed. Install with: pip install PyYAML")
        else:
            logger.error(f"{config_path} not found. Create it from config.yml.example")
    
    def get(self, path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            path: Dot-separated path (e.g., "display.adapter" or "weather.api_key")
            default: Default value if not found
            
        Returns:
            Configuration value or default
            
        Example:
            loader.get("display.adapter")  # Returns "ipixel"
            loader.get("weather.api_key", "")  # Returns API key or empty string
        """
        keys = path.split(".")
        value = self._config
        
        try:
            for key in keys:
                if isinstance(value, dict):
                    value = value[key]
                else:
                    return default
            return value
        except (KeyError, TypeError):
            return default
    
    def get_dict(self, section: str, default: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Get entire configuration section as dictionary.
        
        Args:
            section: Section name (e.g., "weather", "sports")
            default: Default dict if section not found
            
        Returns:
            Dictionary of section configuration
        """
        result = self.get(section)
        if isinstance(result, dict):
            return result
        return default or {}
    
    def get_list(self, path: str, default: Optional[list] = None) -> list:
        """
        Get configuration value as list.
        
        Args:
            path: Dot-separated path
            default: Default list if not found or not a list
            
        Returns:
            List value or default
        """
        value = self.get(path)
        if isinstance(value, list):
            return value
        return default or []
    
    def get_bool(self, path: str, default: bool = False) -> bool:
        """
        Get configuration value as boolean.
        
        Args:
            path: Dot-separated path
            default: Default boolean if not found
            
        Returns:
            Boolean value or default
        """
        value = self.get(path)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "yes", "1", "on")
        return default
    
    def get_int(self, path: str, default: int = 0) -> int:
        """
        Get configuration value as integer.
        
        Args:
            path: Dot-separated path
            default: Default integer if not found or invalid
            
        Returns:
            Integer value or default
        """
        value = self.get(path)
        if isinstance(value, int):
            return value
        try:
            return int(value)
        except (TypeError, ValueError):
            return default
    
    def get_string(self, path: str, default: str = "") -> str:
        """
        Get configuration value as string.
        
        Args:
            path: Dot-separated path
            default: Default string if not found
            
        Returns:
            String value or default
        """
        value = self.get(path)
        if value is None:
            return default
        return str(value)


# Global config instance
_config: Optional[ConfigLoader] = None


def load_config(config_path: Optional[Path] = None) -> ConfigLoader:
    """
    Load configuration and return loader instance.
    
    Args:
        config_path: Path to config.yml file
        
    Returns:
        ConfigLoader instance
    """
    global _config
    _config = ConfigLoader(config_path)
    return _config


def get_config() -> ConfigLoader:
    """
    Get the global config instance.
    
    Call load_config() first to initialize.
    
    Returns:
        ConfigLoader instance
        
    Raises:
        RuntimeError: If config not loaded yet
    """
    global _config
    if _config is None:
        raise RuntimeError("Configuration not loaded. Call load_config() first.")
    return _config


if __name__ == "__main__":
    # Example usage
    config = load_config()
    
    print(f"Adapter: {config.get('display.adapter')}")
    print(f"BLE Addresses: {config.get_list('display.ipixel.ble_addresses')}")
    print(f"Weather City: {config.get_string('weather.city')}")
    print(f"Sports Priority: {config.get_bool('display_modes.sports_priority')}")

