"""
Display Manager using Mode pattern.
"""
import asyncio
from datetime import datetime
import logging
import logging_config

from modes import SportsMode, ClockMode, WeatherMode, StocksMode, TickerMode
from adapters import get_adapter
from config import (
    DISPLAY_CYCLE_MODES,
    DISPLAY_CYCLE_SECONDS,
    DISPLAY_MODE_CHECK_INTERVAL,
    SPORTS_CHECK_INTERVAL,
    SPORTS_MODES,
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


class DisplayManager:
    """
    Manages display modes and cycling logic.
    """
    
    def __init__(self, adapter):
        self.adapter = adapter
        self.modes = {}
        self.cycle_order = []
        self.current_index = 0
        self.current_mode = None
        self.last_mode_switch = datetime.now()
        
        # Build config dict for modes
        self.config = {
            'SPORTS_CHECK_INTERVAL': SPORTS_CHECK_INTERVAL,
            'SPORTS_MODES': SPORTS_MODES,
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
        
        # Initialize modes
        self._init_modes()
    
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
    
    async def run(self):
        """Main display loop"""
        try:
            while True:
                now = datetime.now()
                
                # Determine target mode
                target_mode_name = self._get_next_mode(now)
                target_mode = self.modes[target_mode_name]
                
                # Mode switch?
                if target_mode_name != self.current_mode:
                    logger.info(f"Switching mode: {self.current_mode} → {target_mode_name}")
                    await self.adapter.clear_screen()
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
                elif result.image:
                    await self.adapter.upload_image(result.image, clear_first=False)
                    logger.info(f"{target_mode_name} displayed")
                
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
                                image, panel_idx = static_data
                                logger.info(f"Cycling static to page {target_mode.static_page_index + 1}/{page_count}")
                                await self.adapter.upload_image(image, clear_first=False, panels=[panel_idx])
                                self.last_static_page_update = now
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
            await self.adapter.disconnect()
            logger.info("Disconnected from display")


async def main():
    """Entry point."""
    logger.info("Starting LED Panel Display Manager")
    logger.info(f"Modes: {' → '.join(DISPLAY_CYCLE_MODES)}")
    
    # Initialize adapter
    adapter = get_adapter('ipixel')
    await adapter.connect()
    await adapter.power_on()
    
    # Create and run manager
    manager = DisplayManager(adapter)
    await manager.run()


if __name__ == "__main__":
    asyncio.run(main())