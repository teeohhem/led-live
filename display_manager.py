"""
Display Manager using Mode pattern.
"""
import asyncio
from datetime import datetime
import logging
import logging_config

from modes import SportsMode, ClockMode, WeatherMode, StocksMode
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
                
                if result.image:
                    await self.adapter.upload_image(result.image, clear_first=False)
                    logger.info(f"{target_mode_name} displayed")
                
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