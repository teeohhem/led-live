"""
Hot reload system for config and template changes.

Watches for file changes and triggers reloads without restarting the app.
"""
import asyncio
import logging
from pathlib import Path
from typing import Callable, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

logger = logging.getLogger(__name__)


class ConfigWatcher(FileSystemEventHandler):
    """
    Watches for changes to config and template files.
    """
    
    def __init__(self, callback: Callable, watch_patterns: Set[str]):
        """
        Initialize config watcher.
        
        Args:
            callback: Async function to call when files change
            watch_patterns: Set of file patterns to watch (e.g., {'.yml', '.yaml', '.json'})
        """
        self.callback = callback
        self.watch_patterns = watch_patterns
        self._debounce_task = None
        self._debounce_delay = 1.0  # Wait 1 second before triggering reload
        self._loop = None
    
    def set_event_loop(self, loop):
        """Set the asyncio event loop to use."""
        self._loop = loop
    
    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return
        
        # Check if file matches our watch patterns
        file_path = Path(event.src_path)
        if not any(file_path.name.endswith(pattern) for pattern in self.watch_patterns):
            return
        
        logger.info(f"Detected change: {file_path.name}")
        
        # Debounce: cancel previous reload and schedule new one
        if self._debounce_task:
            self._debounce_task.cancel()
        
        if self._loop:
            self._debounce_task = asyncio.run_coroutine_threadsafe(
                self._debounced_reload(file_path),
                self._loop
            )
    
    async def _debounced_reload(self, file_path: Path):
        """Debounced reload - waits for file changes to settle."""
        try:
            await asyncio.sleep(self._debounce_delay)
            logger.info(f"Triggering reload for: {file_path.name}")
            await self.callback(file_path)
        except asyncio.CancelledError:
            logger.debug("Reload cancelled (debouncing)")
        except Exception as e:
            logger.error(f"Error during reload: {e}")


class HotReloader:
    """
    Manages hot reloading of configuration and templates.
    """
    
    def __init__(self, on_reload_callback: Callable):
        """
        Initialize hot reloader.
        
        Args:
            on_reload_callback: Async function to call when reload is needed
        """
        self.on_reload = on_reload_callback
        self.observer = Observer()
        self.watcher = None
        self._started = False
    
    def start(self, watch_paths: list[str] = None, watch_patterns: Set[str] = None):
        """
        Start watching for file changes.
        
        Args:
            watch_paths: List of paths to watch (default: current directory)
            watch_patterns: File extensions to watch (default: {'.yml', '.yaml', '.json'})
        """
        if self._started:
            logger.warning("Hot reloader already started")
            return
        
        if watch_paths is None:
            watch_paths = ['.']
        
        if watch_patterns is None:
            watch_patterns = {'.yml', '.yaml', '.json'}
        
        # Create watcher
        self.watcher = ConfigWatcher(self.on_reload, watch_patterns)
        self.watcher.set_event_loop(asyncio.get_event_loop())
        
        # Schedule watches
        for path in watch_paths:
            path_obj = Path(path)
            if path_obj.exists():
                self.observer.schedule(self.watcher, str(path_obj), recursive=True)
                logger.info(f"Watching for changes: {path_obj}")
        
        # Start observer thread
        self.observer.start()
        self._started = True
        logger.info(f"Hot reload enabled (watching: {', '.join(watch_patterns)})")
    
    def stop(self):
        """Stop watching for file changes."""
        if self._started:
            self.observer.stop()
            self.observer.join()
            self._started = False
            logger.info("Hot reload stopped")


async def reload_with_retry(reload_func: Callable, max_retries: int = 3):
    """
    Execute reload with retry logic.
    
    Args:
        reload_func: Async function to call for reload
        max_retries: Maximum number of retry attempts
    """
    for attempt in range(max_retries):
        try:
            await reload_func()
            logger.info("✓ Reload successful")
            return
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Reload failed (attempt {attempt + 1}/{max_retries}): {e}")
                await asyncio.sleep(1)  # Wait before retry
            else:
                logger.error(f"✗ Reload failed after {max_retries} attempts: {e}")
                raise

