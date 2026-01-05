"""
Display Manager using Mode pattern.
"""
import asyncio
from datetime import datetime
import logging
import logging_config
from pathlib import Path

from modes import SportsMode, ClockMode, WeatherMode, StocksMode, TickerMode
from adapters import get_adapter
from config import (
    DISPLAY_CYCLE_MODES,
    DISPLAY_CYCLE_SECONDS,
    DISPLAY_MODE_CHECK_INTERVAL,
    SPORTS_CHECK_INTERVAL,
    SPORTS_MODES,
    SPORTS_LIVE_GAMES_SOURCE,
    SPORTS_LIVE_GAMES_LEAGUES,
    SPORTS_GAMES_PER_PAGE,
    SPORTS_GAMES_CYCLE_INTERVAL,
    SPORTS_SHOW_LOGOS,
    WEATHER_CHECK_INTERVAL,
    STOCKS_CHECK_INTERVAL,
    CLOCK_THEME,
    CLOCK_24H,
    WEATHER_FORECAST_MODE,
    DISPLAY_SPORTS_PRIORITY,
    DISPLAY_SPORTS_REFRESH_INTERVAL,
    DISPLAY_WEATHER_REFRESH_INTERVAL,
    DISPLAY_CLOCK_REFRESH_INTERVAL,
    DISPLAY_STOCKS_REFRESH_INTERVAL,
    TICKER_MODES,
    TICKER_SCROLL_SPEED,
    TICKER_REFRESH_INTERVAL,
    TICKER_HEIGHT,
)

logger = logging.getLogger('led_panel.display_manager')

# Hot reload support (optional)
try:
    from hot_reload import HotReloader, reload_with_retry
    HOT_RELOAD_AVAILABLE = True
except ImportError:
    HOT_RELOAD_AVAILABLE = False
    logger.debug("Hot reload not available (watchdog not installed)")


class DisplayManager:
    """
    Manages display modes and cycling logic.
    """
    
    def __init__(self, adapter, enable_hot_reload=True):
        self.adapter = adapter
        self.modes = {}
        self.cycle_order = []
        self.current_index = 0
        self.current_mode = None
        self.last_mode_switch = datetime.now()
        self.hot_reloader = None
        
        # Build config dict for modes
        self._load_config()
        
        # Initialize modes
        self._init_modes()
        
        # Setup hot reload if requested and available
        if enable_hot_reload and HOT_RELOAD_AVAILABLE:
            self._setup_hot_reload()
    
    def _load_config(self):
        """Load configuration from config module."""
        self.config = {
            'SPORTS_CHECK_INTERVAL': SPORTS_CHECK_INTERVAL,
            'SPORTS_MODES': SPORTS_MODES,
            'SPORTS_LIVE_GAMES_SOURCE': SPORTS_LIVE_GAMES_SOURCE,
            'SPORTS_LIVE_GAMES_LEAGUES': SPORTS_LIVE_GAMES_LEAGUES,
            'SPORTS_GAMES_PER_PAGE': SPORTS_GAMES_PER_PAGE,
            'SPORTS_GAMES_CYCLE_INTERVAL': SPORTS_GAMES_CYCLE_INTERVAL,
            'SPORTS_SHOW_LOGOS': SPORTS_SHOW_LOGOS,
            'WEATHER_CHECK_INTERVAL': WEATHER_CHECK_INTERVAL,
            'STOCKS_CHECK_INTERVAL': STOCKS_CHECK_INTERVAL,
            'DISPLAY_SPORTS_PRIORITY': DISPLAY_SPORTS_PRIORITY,
            'DISPLAY_SPORTS_REFRESH_INTERVAL': DISPLAY_SPORTS_REFRESH_INTERVAL,
            'DISPLAY_WEATHER_REFRESH_INTERVAL': DISPLAY_WEATHER_REFRESH_INTERVAL,
            'DISPLAY_CLOCK_REFRESH_INTERVAL': DISPLAY_CLOCK_REFRESH_INTERVAL,
            'DISPLAY_STOCKS_REFRESH_INTERVAL': DISPLAY_STOCKS_REFRESH_INTERVAL,
            'CLOCK_THEME': CLOCK_THEME,
            'CLOCK_24H': CLOCK_24H,
            'WEATHER_FORECAST_MODE': WEATHER_FORECAST_MODE,
            'TICKER_MODES': TICKER_MODES,
            'TICKER_SCROLL_SPEED': TICKER_SCROLL_SPEED,
            'TICKER_REFRESH_INTERVAL': TICKER_REFRESH_INTERVAL,
            'TICKER_HEIGHT': TICKER_HEIGHT,
        }
    
    def _setup_hot_reload(self):
        """Setup hot reload watcher."""
        try:
            self.hot_reloader = HotReloader(self._handle_file_change)
            # Watch current directory and core/layout for changes
            watch_paths = ['.', 'core/layout']
            watch_patterns = {'.yml', '.yaml', '.json'}
            self.hot_reloader.start(watch_paths, watch_patterns)
        except Exception as e:
            logger.warning(f"Could not enable hot reload: {e}")
    
    def _init_modes(self):
        """Initialize all configured modes."""
        mode_classes = {
            'sports': SportsMode,
            'clock': ClockMode,
            'weather': WeatherMode,
            'stocks': StocksMode,
            'ticker': TickerMode,
        }
        
        for mode_name in DISPLAY_CYCLE_MODES:
            if mode_name in mode_classes:
                self.modes[mode_name] = mode_classes[mode_name](self.config)
                self.cycle_order.append(mode_name)
                logger.info(f"Initialized {mode_name} mode")
    
    async def _handle_file_change(self, file_path: Path):
        """
        Handle file change events (config or template changes).
        
        Args:
            file_path: Path to the changed file
        """
        logger.info(f"🔄 Reloading due to change in: {file_path.name}")
        
        # Determine what changed
        if file_path.name == 'config.yml':
            await reload_with_retry(self._reload_config)
        elif file_path.suffix in {'.json', '.yaml', '.yml'}:
            # Template or other config file changed
            await reload_with_retry(self._reload_templates)
    
    async def _reload_config(self):
        """Reload configuration and reinitialize modes."""
        logger.info("Reloading configuration...")
        
        # Reload config module
        import importlib
        import config
        importlib.reload(config)
        
        # Reload config variables
        from config import (
            DISPLAY_CYCLE_MODES as new_cycle_modes,
            DISPLAY_CYCLE_SECONDS as new_cycle_seconds,
            SPORTS_CHECK_INTERVAL as new_sports_check,
            SPORTS_MODES as new_sports_modes,
            SPORTS_LIVE_GAMES_SOURCE as new_live_source,
            SPORTS_LIVE_GAMES_LEAGUES as new_live_leagues,
            SPORTS_GAMES_PER_PAGE as new_games_per_page,
            SPORTS_GAMES_CYCLE_INTERVAL as new_games_cycle,
            SPORTS_SHOW_LOGOS as new_show_logos,
            WEATHER_CHECK_INTERVAL as new_weather_check,
            STOCKS_CHECK_INTERVAL as new_stocks_check,
            CLOCK_THEME as new_clock_theme,
            CLOCK_24H as new_clock_24h,
            WEATHER_FORECAST_MODE as new_weather_forecast,
            DISPLAY_SPORTS_PRIORITY as new_sports_priority,
            DISPLAY_SPORTS_REFRESH_INTERVAL as new_sports_refresh,
            DISPLAY_WEATHER_REFRESH_INTERVAL as new_weather_refresh,
            DISPLAY_CLOCK_REFRESH_INTERVAL as new_clock_refresh,
            DISPLAY_STOCKS_REFRESH_INTERVAL as new_stocks_refresh,
            TICKER_MODES as new_ticker_modes,
            TICKER_SCROLL_SPEED as new_ticker_speed,
            TICKER_REFRESH_INTERVAL as new_ticker_refresh,
            TICKER_HEIGHT as new_ticker_height,
        )
        
        # Update globals (for module-level access)
        global DISPLAY_CYCLE_MODES, DISPLAY_CYCLE_SECONDS
        DISPLAY_CYCLE_MODES = new_cycle_modes
        DISPLAY_CYCLE_SECONDS = new_cycle_seconds
        
        # Rebuild config dict
        self.config = {
            'SPORTS_CHECK_INTERVAL': new_sports_check,
            'SPORTS_MODES': new_sports_modes,
            'SPORTS_LIVE_GAMES_SOURCE': new_live_source,
            'SPORTS_LIVE_GAMES_LEAGUES': new_live_leagues,
            'SPORTS_GAMES_PER_PAGE': new_games_per_page,
            'SPORTS_GAMES_CYCLE_INTERVAL': new_games_cycle,
            'SPORTS_SHOW_LOGOS': new_show_logos,
            'WEATHER_CHECK_INTERVAL': new_weather_check,
            'STOCKS_CHECK_INTERVAL': new_stocks_check,
            'DISPLAY_SPORTS_PRIORITY': new_sports_priority,
            'DISPLAY_SPORTS_REFRESH_INTERVAL': new_sports_refresh,
            'DISPLAY_WEATHER_REFRESH_INTERVAL': new_weather_refresh,
            'DISPLAY_CLOCK_REFRESH_INTERVAL': new_clock_refresh,
            'DISPLAY_STOCKS_REFRESH_INTERVAL': new_stocks_refresh,
            'CLOCK_THEME': new_clock_theme,
            'CLOCK_24H': new_clock_24h,
            'WEATHER_FORECAST_MODE': new_weather_forecast,
            'TICKER_MODES': new_ticker_modes,
            'TICKER_SCROLL_SPEED': new_ticker_speed,
            'TICKER_REFRESH_INTERVAL': new_ticker_refresh,
            'TICKER_HEIGHT': new_ticker_height,
        }
        
        # Reinitialize modes with new config
        old_modes = self.modes.copy()
        self.modes.clear()
        self.cycle_order.clear()
        self._init_modes()
        
        # Force mode switch on next iteration
        self.current_mode = None
        
        logger.info(f"Configuration reloaded (modes: {', '.join(self.cycle_order)})")
    
    async def _reload_templates(self):
        """Reload layout templates without restarting."""
        logger.info("Reloading templates...")
        
        # Reinitialize modes (they will reload templates)
        mode_classes = {
            'sports': SportsMode,
            'clock': ClockMode,
            'weather': WeatherMode,
            'stocks': StocksMode,
            'ticker': TickerMode,
        }
        
        # Recreate modes that use templates
        for mode_name in list(self.modes.keys()):
            if mode_name in mode_classes:
                logger.info(f"Reinitializing {mode_name} mode...")
                self.modes[mode_name] = mode_classes[mode_name](self.config)
        
        # Force mode switch on next iteration to see changes
        self.current_mode = None
        
        logger.info("Templates reloaded")
    
    def _get_priority_mode(self):
        """Check if any mode has priority (e.g., live sports)."""
        for mode_name, mode in self.modes.items():
            if mode.has_priority():
                return mode_name
        return None
    
    def _get_next_mode(self, now: datetime):
        """Determine next mode based on priority or cycling."""
        # Check for priority mode first
        priority_mode = self._get_priority_mode()
        if priority_mode:
            logger.info(f"Priority mode active: {priority_mode}")
            return priority_mode
        
        # Check if it's time to cycle
        time_since_switch = (now - self.last_mode_switch).total_seconds()
        if time_since_switch >= DISPLAY_CYCLE_SECONDS:
            # Cycle to next mode
            self.current_index = (self.current_index + 1) % len(self.cycle_order)
            self.last_mode_switch = now
            logger.info(f"Cycling to next mode")
        
        return self.cycle_order[self.current_index]
    
    async def _upload_multi_panel_ticker_gifs(self, panel_gifs):
        """
        Upload GIFs to multiple panels in parallel for synchronized start.
        
        Args:
            panel_gifs: List of GIF bytes, one per panel
        """
        logger.info(f"Uploading {len(panel_gifs)} ticker GIFs to panels (parallel)...")
        
        # Upload all GIFs in parallel so they start together
        upload_tasks = []
        for panel_idx, gif_bytes in enumerate(panel_gifs):
            if gif_bytes:
                size_kb = len(gif_bytes) / 1024
                logger.info(f"Preparing panel {panel_idx} ticker ({size_kb:.1f} KB)")
                # Create upload task
                task = self.adapter.upload_gif(gif_bytes, panels=[panel_idx])
                upload_tasks.append(task)
        
        # Upload all panels simultaneously
        if upload_tasks:
            await asyncio.gather(*upload_tasks)
        
        logger.info("All ticker GIFs uploaded - panels are now looping in sync!")
    
    async def _ensure_connection(self) -> bool:
        """
        Ensure display connection is healthy, reconnecting if needed.
        Returns True if connected, False if all reconnection attempts failed.
        """
        try:
            if await self.adapter.ensure_connected():
                return True
            else:
                logger.error("Failed to establish connection to display")
                return False
        except Exception as e:
            logger.error(f"Connection check failed: {e}")
            return False

    async def run(self):
        """Main display loop"""
        try:
            while True:
                now = datetime.now()
                
                # Ensure we're connected before doing anything
                if not await self._ensure_connection():
                    logger.warning("Display not connected - waiting 10 seconds before retry...")
                    await asyncio.sleep(10)
                    continue
                
                # Determine target mode
                target_mode_name = self._get_next_mode(now)
                target_mode = self.modes[target_mode_name]
                
                # Mode switch?
                if target_mode_name != self.current_mode:
                    logger.info(f"Switching mode: {self.current_mode} → {target_mode_name}")
                    try:
                        await self.adapter.clear_screen()
                    except Exception as e:
                        logger.error(f"Failed to clear screen: {e}")
                        # Connection might be lost - next iteration will check
                        continue
                    target_mode.reset_state()
                    self.current_mode = target_mode_name
                
                # Update the mode (fetch data, render if needed)
                result = await target_mode.update(
                    self.adapter.display_width,
                    self.adapter.display_height,
                    now
                )
                
                # Handle result
                if result.should_skip:
                    logger.info(f"{target_mode_name} has no data - skipping to next mode")
                    self.current_index = (self.current_index + 1) % len(self.cycle_order)
                    self.last_mode_switch = now
                    self.current_mode = None
                    continue
                
                # Special handling for ticker mode (uses GIF for smooth playback)
                if target_mode_name == 'ticker':
                    try:
                        # Check layout type
                        if target_mode.layout == 'multi':
                            # Ticker + static panel mode with page cycling
                            ticker_data = target_mode.get_ticker_gif_with_panel()
                            static_data = target_mode.get_static_image_with_panel()
                            page_count = target_mode.get_static_page_count()
                            
                            logger.info(f"Uploading ticker + static panel ({page_count} pages)...")
                            
                            # Upload ticker GIF and static image in parallel
                            tasks = []
                            
                            if ticker_data:
                                gif_bytes, panel_idx = ticker_data
                                logger.info(f"Ticker GIF: {len(gif_bytes)/1024:.1f} KB → panel {panel_idx} (looping)")
                                tasks.append(self.adapter.upload_gif(gif_bytes, panels=[panel_idx]))
                            
                            if static_data:
                                image, panel_idx = static_data
                                logger.info(f"Static page {target_mode.static_page_index + 1}/{page_count} → panel {panel_idx}")
                                tasks.append(self.adapter.upload_image(image, clear_first=False, panels=[panel_idx]))
                            
                            # Upload both in parallel with timeout
                            if tasks:
                                try:
                                    await asyncio.wait_for(
                                        asyncio.gather(*tasks),
                                        timeout=30.0  # 30 second timeout
                                    )
                                    logger.info("Ticker + static uploaded!")
                                except asyncio.TimeoutError:
                                    logger.error("Upload timed out after 30 seconds - GIF might be too large!")
                                    logger.info("Skipping to next mode...")
                                    continue
                            
                            # Track when we last updated the static page
                            if not hasattr(self, 'last_static_page_update'):
                                self.last_static_page_update = now
                        else:
                            # Single panel mode
                            gif_bytes = target_mode.get_gif_bytes()
                            if gif_bytes:
                                logger.info(f"Uploading ticker GIF ({len(gif_bytes)/1024:.1f} KB)")
                                await self.adapter.upload_gif(gif_bytes)
                                logger.info("Ticker GIF uploaded (looping on display)")
                    except Exception as e:
                        logger.error(f"Failed to upload ticker: {e}")
                        # Connection likely lost - next iteration will reconnect
                        continue
                elif result.image:
                    try:
                        await self.adapter.upload_image(result.image, clear_first=False)
                        logger.info(f"{target_mode_name} displayed")
                    except Exception as e:
                        logger.error(f"Failed to upload {target_mode_name} image: {e}")
                        # Connection likely lost - next iteration will reconnect
                        continue
                
                # Handle static page cycling for ticker mode
                if (target_mode_name == 'ticker' and 
                    target_mode.layout == 'multi' and 
                    hasattr(self, 'last_static_page_update')):
                    
                    page_count = target_mode.get_static_page_count()
                    logger.debug(f"Ticker page cycling check: {page_count} pages")
                    
                    if page_count > 1:
                        # Check if it's time to cycle to next page
                        time_since_page_update = (now - self.last_static_page_update).total_seconds()
                        logger.debug(f"Time since page update: {time_since_page_update:.1f}s / {target_mode.static_page_duration}s")
                        
                        if time_since_page_update >= target_mode.static_page_duration:
                            # Advance to next page
                            target_mode.advance_static_page()
                            static_data = target_mode.get_static_image_with_panel()
                            if static_data:
                                try:
                                    image, panel_idx = static_data
                                    logger.info(f"Cycling static to page {target_mode.static_page_index + 1}/{page_count}")
                                    await self.adapter.upload_image(image, clear_first=False, panels=[panel_idx])
                                    self.last_static_page_update = now
                                except Exception as e:
                                    logger.error(f"Failed to cycle static page: {e}")
                                    # Connection likely lost - next iteration will reconnect
                                    continue
                            else:
                                logger.warning("No static data available for page cycling")
                    else:
                        logger.debug(f"Only 1 page, no cycling needed")
                
                # Wait before next check
                await asyncio.sleep(DISPLAY_MODE_CHECK_INTERVAL)
        
        except KeyboardInterrupt:
            logger.info("\nShutting down gracefully...")
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Stop hot reloader
            if self.hot_reloader:
                self.hot_reloader.stop()
            
            await self.adapter.disconnect()
            logger.info("Disconnected from display")


async def main():
    """Entry point."""
    logger.info("Starting LED Panel Display Manager")
    logger.info(f"Modes: {' → '.join(DISPLAY_CYCLE_MODES)}")
    
    # Initialize adapter
    adapter = get_adapter('ipixel')
    
    try:
        # Connect with built-in retry logic
        await adapter.connect()
        await adapter.power_on()
        
        # Create and run manager
        manager = DisplayManager(adapter)
        await manager.run()
    except KeyboardInterrupt:
        logger.info("\nShutting down gracefully...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Ensure cleanup
        try:
            if adapter.is_connected:
                await adapter.disconnect()
        except:
            pass


if __name__ == "__main__":
    asyncio.run(main())