"""
Display adapters package.

This package contains display adapter implementations for different LED panel protocols.
"""

# Lazy imports to avoid PIL dependency during testing
def __getattr__(name):
    if name in ('DisplayAdapter', 'DisplayError', 'ConnectionError', 'UploadError'):
        from .base import DisplayAdapter, DisplayError, ConnectionError, UploadError
        return locals()[name]
    elif name in ('get_adapter', 'list_available_adapters', 'get_default_adapter_name'):
        from .loader import get_adapter, list_available_adapters, get_default_adapter_name
        return locals()[name]
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    'DisplayAdapter',
    'DisplayError',
    'ConnectionError',
    'UploadError',
    'get_adapter',
    'list_available_adapters',
    'get_default_adapter_name'
]
