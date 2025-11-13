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
    
    async def _play_ticker_frames(self, frames):
        """Play ticker animation frames at 30 FPS."""
        from adapters.ipixel.protocol import upload_png
        
        frame_rate = 30  # FPS
        frame_delay = 1.0 / frame_rate
        
        for frame in frames:
            await upload_png(self.adapter.client, frame, clear_first=False)
            await asyncio.sleep(frame_delay)
    
    async def _play_multi_panel_ticker(self, panel_frames_list):
        """
        Play multi-panel ticker with synchronized scrolling.
        
        Args:
            panel_frames_list: List of frame lists, one per panel
                               [[panel0_frame1, panel0_frame2, ...],
                                [panel1_frame1, panel1_frame2, ...]]
        """
        from adapters.ipixel.protocol import upload_png
        
        # Find max frame count (for synchronization)
        max_frames = max(len(frames) for frames in panel_frames_list)
        
        logger.info(f"Multi-panel ticker: {len(panel_frames_list)} panels, {max_frames} frames (synchronized)")
        
        frame_rate = 30  # FPS
        frame_delay = 1.0 / frame_rate
        
        # Play frames synchronized across all panels
        for frame_idx in range(max_frames):
            # Upload to each panel
            for panel_idx, panel_frames in enumerate(panel_frames_list):
                # Loop shorter tickers
                frame = panel_frames[frame_idx % len(panel_frames)]
                await upload_png(self.adapter.client, frame, clear_first=False, panels=[panel_idx])
            
            # Wait for next frame
            await asyncio.sleep(frame_delay)
    
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
                
                # Special handling for ticker mode (plays frames)
                if target_mode_name == 'ticker':
                    # Check if multi-panel ticker
                    if hasattr(target_mode, 'get_panel_frames') and target_mode.layout == 'multi':
                        panel_frames = target_mode.get_panel_frames()
                        if panel_frames:
                            logger.info(f"Playing multi-panel ticker: {len(panel_frames)} panels")
                            await self._play_multi_panel_ticker(panel_frames)
                            logger.info("Multi-panel ticker playback complete")
                    elif hasattr(target_mode, 'get_frames'):
                        frames = target_mode.get_frames()
                        if frames:
                            logger.info(f"Playing ticker: {len(frames)} frames")
                            await self._play_ticker_frames(frames)
                            logger.info("Ticker playback complete")
                elif result.image:
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