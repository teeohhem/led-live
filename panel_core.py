"""
Core panel functionality - Display Adapter Management
=====================================================

This module provides the core display adapter management functionality for the LED panel system.
It handles adapter lifecycle and provides a clean interface for display operations.

Key Features:
- DisplayAdapter lifecycle management
- Global adapter state management
- Clean adapter interface

Shared by all display applications (sports, weather, clock, etc.)
"""
from typing import Optional

from adapters.base import DisplayAdapter

# --- Display Adapter Management ---
_display_adapter: Optional[DisplayAdapter] = None

def set_display_adapter(adapter: DisplayAdapter) -> None:
    """Set the display adapter to use for all operations."""
    global _display_adapter
    _display_adapter = adapter

def get_display_adapter() -> Optional[DisplayAdapter]:
    """Get the current display adapter."""
    return _display_adapter


