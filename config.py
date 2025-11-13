"""
Centralized configuration module for LED Panel Display System.

This module loads all configuration from config.yml at startup and provides
simple module-level variables that can be imported directly by other modules.

Example:
    from config import WEATHER_API_KEY, SPORTS_CHECK_INTERVAL, DISPLAY_CYCLE_MODES
    
This avoids having config loading code scattered throughout the codebase.
"""

import logging
from config_loader import load_config
from typing import List, Dict, Any

logger = logging.getLogger('led_panel.config')

# Load config.yml
try:
    _cfg = load_config()
except Exception as e:
    logger.error(f"Failed to load config.yml: {e}")
    raise RuntimeError("Configuration failed to load. Check config.yml exists and is valid YAML.")

# ============================================================================
# DISPLAY ADAPTER SETTINGS
# ============================================================================
ADAPTER_TYPE: str = _cfg.get_string("display.adapter", "ipixel")

# iPixel Panel Settings
IPIXEL_BLE_ADDRESSES: List[str] = _cfg.get_list("display.ipixel.ble_addresses", [])
IPIXEL_BLE_UUID_WRITE: str = _cfg.get_string("display.ipixel.ble_uuid_write", "0000fa02-0000-1000-8000-00805f9b34fb")
IPIXEL_PANEL_WIDTH: int = _cfg.get_int("display.ipixel.size_width", 64)
IPIXEL_PANEL_HEIGHT: int = _cfg.get_int("display.ipixel.size_height", 20)

# ============================================================================
# WEATHER SETTINGS
# ============================================================================
WEATHER_API_KEY: str = _cfg.get_string("weather.api_key", "your-api-key-here")
WEATHER_CITY: str = _cfg.get_string("weather.city", "Detroit,US")
WEATHER_UNITS: str = _cfg.get_string("weather.units", "imperial")
WEATHER_FORECAST_MODE: str = _cfg.get_string("weather.forecast_mode", "daily")
WEATHER_SHOW_ICONS: bool = _cfg.get_bool("weather.show_icons", True)
WEATHER_CHECK_INTERVAL: int = _cfg.get_int("weather.check_interval", 1800)

# ============================================================================
# SPORTS SETTINGS
# ============================================================================
SPORTS_NHL_TEAMS: List[str] = _cfg.get_list("sports.teams.nhl", ["DET"])
SPORTS_NBA_TEAMS: List[str] = _cfg.get_list("sports.teams.nba", ["DET"])
SPORTS_NFL_TEAMS: List[str] = _cfg.get_list("sports.teams.nfl", ["DET"])
SPORTS_MLB_TEAMS: List[str] = _cfg.get_list("sports.teams.mlb", ["DET"])
SPORTS_TEST_MODE: bool = _cfg.get_bool("sports.test_mode", False)
SPORTS_CHECK_INTERVAL: int = _cfg.get_int("sports.check_interval", 10)
SPORTS_SHOW_LOGOS: bool = _cfg.get_bool("sports.show_logos", True)
SPORTS_MODES: List[str] = _cfg.get_list("sports.modes", ["live", "upcoming"])

# ============================================================================
# STOCKS SETTINGS
# ============================================================================
STOCKS_SYMBOLS: List[str] = _cfg.get_list("stocks.symbols", ["AAPL", "GOOGL", "MSFT"])
STOCKS_CHECK_INTERVAL: int = _cfg.get_int("stocks.check_interval", 300)

# ============================================================================
# DISPLAY MODES SETTINGS
# ============================================================================
DISPLAY_SPORTS_PRIORITY: bool = _cfg.get_bool("display_modes.sports_priority", True)
DISPLAY_CYCLE_MODES: List[str] = _cfg.get_list("display_modes.cycle_modes", ["clock", "weather"])
DISPLAY_CYCLE_SECONDS: int = _cfg.get_int("display_modes.cycle_seconds", 300)
CLOCK_THEME: str = _cfg.get_string("display_modes.clock_theme", "stranger_things")
CLOCK_24H: bool = _cfg.get_bool("display_modes.clock_24h", False)
DISPLAY_MODE_CHECK_INTERVAL: int = _cfg.get_int("display_modes.mode_check_interval", 2)

# Display refresh intervals
DISPLAY_SPORTS_REFRESH_INTERVAL: int = _cfg.get_int("display_modes.sports_refresh_interval", 2)
DISPLAY_WEATHER_REFRESH_INTERVAL: int = _cfg.get_int("display_modes.weather_refresh_interval", 2)
DISPLAY_CLOCK_REFRESH_INTERVAL: int = _cfg.get_int("display_modes.clock_refresh_interval", 2)
DISPLAY_STOCKS_REFRESH_INTERVAL: int = _cfg.get_int("display_modes.stocks_refresh_interval", 2)

# ============================================================================
# POWER MANAGEMENT SETTINGS
# ============================================================================
POWER_AUTO_OFF: bool = _cfg.get_bool("power.auto_off", True)
POWER_OFF_TIME: str = _cfg.get_string("power.off_time", "24:00")
POWER_ON_TIME: str = _cfg.get_string("power.on_time", "07:00")

# ============================================================================
# CLOCK THEMES
# ============================================================================
CLOCK_THEMES: Dict[str, Any] = _cfg.get_dict("clock_themes", {})

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_all_config() -> Dict[str, Any]:
    """Get the entire configuration dictionary."""
    return _cfg._config


def get_config_value(path: str, default: Any = None) -> Any:
    """
    Get a configuration value using dot notation.
    
    Args:
        path: Dot-separated path (e.g., "sports.check_interval")
        default: Default value if not found
        
    Returns:
        Configuration value or default
    """
    return _cfg.get(path, default)


# ============================================================================
# VALIDATION AND STARTUP
# ============================================================================

# Validate critical config values
if not IPIXEL_BLE_ADDRESSES:
    logger.warning("No BLE addresses configured in config.yml")
    logger.warning("Set display.ipixel.ble_addresses to your panel addresses")
    logger.warning("See config.yml.example for the format")

logger.info("Configuration loaded successfully")
logger.debug(f"Adapter: {ADAPTER_TYPE}")
logger.debug(f"Weather city: {WEATHER_CITY}")
logger.debug(f"Display modes: {', '.join(DISPLAY_CYCLE_MODES)}")
logger.debug(f"Clock theme: {CLOCK_THEME}")
if IPIXEL_BLE_ADDRESSES:
    logger.debug(f"BLE panels: {len(IPIXEL_BLE_ADDRESSES)}")

