# Changelog

## [2.1.0] - Documentation Reorganization & Stocks Mode - 2024-11-10

### Added
- **Stock Market Mode**
  - Display stock tickers via Yahoo Finance (yfinance)
  - Color-coded price changes (green up, red down)
  - Configurable symbols via `STOCKS_SYMBOLS`
  - Adaptive layouts for 1-4 stocks
  - Auto-refresh at configurable intervals

- **JSON-Based Custom Clock Themes**
  - Create custom themes without code changes
  - `custom_themes.json` for user-defined themes
  - `custom_themes.json.example` with example themes
  - Automatic loading and merging with built-in themes
  - Multiple themes in one file support
  - Custom themes override built-in if same name

- **Comprehensive Documentation**
  - Created `docs/` folder for all comprehensive guides
  - `docs/setup.md` - Detailed 5-minute setup guide
  - `docs/configuration.md` - Complete configuration reference
  - `docs/clock_themes.md` - Clock theme customization guide
  - `docs/README.md` - Documentation index

### Changed
- **Documentation Structure**
  - Moved all comprehensive docs to `docs/` folder
  - `README.md` remains as main entry point
  - `CHANGELOG.md` stays in root (standard practice)
  - Consolidated scattered docs into cohesive guides:
    - Merged `CONFIG_REFERENCE.md`, `ENV_VARS.md`, `DISPLAY_MODES.md` → `docs/configuration.md`
    - Moved `SETUP.md` → `docs/setup.md`
    - Moved `CLOCK_THEMES.md` → `docs/clock_themes.md`
  - Removed `OPEN_SOURCE_READY.md` (work summary, no longer needed)

- **Sports Display Refactoring**
  - Renamed rendering functions for clarity:
    - `render_scoreboard_single_game_fullscreen()` - 1 game with logos
    - `render_scoreboard_two_games_expanded()` - 2 games, detailed layout
    - `render_scoreboard_multi_game_compact()` - 3-4 games, compact layout
  - Fixed panel boundary positioning for 3-4 game layouts
  - Improved spacing to prevent text bleeding across panels

- **Display Manager Improvements**
  - Conditional sports data fetching (only when needed)
  - Fixed stocks mode not displaying on startup
  - Better startup banner showing active modes and symbols
  - Improved mode validation and error messages

### Fixed
- **Stocks Mode Issues**
  - Fixed `last_stocks_check` initialization (now fetches immediately)
  - Sports no longer checked when not in `DISPLAY_CYCLE_MODES`
  - Stocks mode now displays properly when configured

- **Sports Layout Issues**
  - Fixed middle game bleeding across panel boundary in 3-game layout
  - Improved vertical spacing (positions: `[1, 9, 22]` for 3 games)
  - Better space utilization in compact layouts

### Documentation
- Single source of truth: `README.md` is main entry
- Comprehensive guides in `docs/` folder
- Clear separation: quick start vs. detailed reference
- All internal doc references updated

---

## [2.0.0] - Environment Variable Configuration - 2024-11-10

### Added
- **Environment variable configuration system**
  - `config.env.example` - Template with all configuration options
  - `config.env` - User's actual config (git-ignored)
  - Simple built-in parser (no external dependencies)
  - Support for both file-based and system environment variables

- **New documentation**
  - `ENV_VARS.md` - Complete environment variable guide
  - `SETUP.md` - Quick 5-minute setup guide
  - Updated `README.md` with configuration section

### Changed
- **panel_core.py**
  - `BLE_ADDRESS_TOP` now loads from `BLE_ADDRESS_TOP` env var
  - `BLE_ADDRESS_BOTTOM` now loads from `BLE_ADDRESS_BOTTOM` env var
  - `UUID_WRITE_DATA` now loads from `BLE_UUID_WRITE` env var
  - Removed hardcoded BLE addresses

- **weather_data.py**
  - `OPENWEATHER_API_KEY` now loads from env var
  - `CITY` now loads from `WEATHER_CITY` env var
  - Removed hardcoded API key

- **sports_data.py**
  - Team filtering now uses environment variables:
    - `SPORTS_NHL_TEAMS` (comma-separated)
    - `SPORTS_NBA_TEAMS` (comma-separated)
    - `SPORTS_NFL_TEAMS` (comma-separated)
    - `SPORTS_MLB_TEAMS` (comma-separated)
  - Removed hardcoded Detroit team list
  - Support for following multiple teams per league

- **display_manager.py**
  - `CLOCK_THEME` now loads from env var
  - `CLOCK_24H` now loads from env var
  - `WEATHER_FORECAST_MODE` now loads from env var

### Security
- **All sensitive data removed from code**
  - No hardcoded BLE addresses
  - No hardcoded API keys
  - No hardcoded team preferences
  - `config.env` added to `.gitignore`
  - Template provided in `config.env.example`

### Documentation
- Updated `README.md` with configuration instructions
- Updated `OPEN_SOURCE_READY.md` with security checklist
- Added comprehensive environment variable guide
- Added quick setup guide for new users

---

## [1.0.0] - Clean Codebase - 2024-11-10

### Removed
- **Dead code from panel_core.py**
  - `PIXEL_DELAY` constant (unused)
  - `ENABLE_DIY` command (unused)
  - `build_set_time_cmd()` (replaced by PNG clock)
  - `build_clock_mode_cmd()` (replaced by PNG clock)
  - `string_to_bitmaps()` (bulk text doesn't work)
  - `build_string_packet()` (bulk text doesn't work)
  - `send_text_bulk()` (bulk text doesn't work)
  - Unused imports (`ImageDraw`, `ImageFont`)

- **Dead code from display_manager.py**
  - Unused `ImageFont` import
  - Unused `CLEAR_SCREEN` import

### Changed
- **Code organization**
  - Moved pixel-by-pixel code to `legacy/legacy_utils.py`
  - Moved old display files to `legacy/`
  - Archived all test/experimental code to `legacy/tests/`
  - Created clear separation between active and legacy code

### Added
- **Documentation**
  - `README.md` - Comprehensive project documentation
  - `LICENSE` - MIT License
  - `requirements.txt` - Project dependencies
  - `.gitignore` - Git ignore rules
  - `CLEANUP_SUMMARY.md` - Architecture overview
  - `OPEN_SOURCE_READY.md` - Release checklist
  - `legacy/README.md` - Legacy code documentation

### Quality
- ✅ 0 linter errors
- ✅ 0 unused imports
- ✅ 0 dead code paths
- ✅ All functions documented
- ✅ Clean, focused codebase (~1,500 lines vs ~3,500 before)

---

## Earlier History

### [0.9.0] - PNG Rendering
- Implemented PNG upload for instant display updates
- 100x faster than pixel-by-pixel rendering
- Full PIL image support

### [0.8.0] - Custom Clock Themes
- Replaced unreliable built-in clock
- Created themed clock system (Stranger Things, Matrix, Classic)
- Integrated with weather display

### [0.7.0] - Team Logos
- Added team logo support
- Automatic aspect ratio preservation
- Transparent border cropping
- League-specific folder organization

### [0.6.0] - Live Game Priority
- Implemented live game filtering
- Auto-switches to sports when games are live
- Intelligent layout selection

### [0.5.0] - Weather Integration
- OpenWeatherMap API integration
- Hourly and daily forecast support
- Temperature color coding
- Weather icons

### [0.4.0] - Dual Panel Support
- Implemented dual 64x20 panel support (64x40 total)
- Smart panel boundary handling
- Automatic image splitting

### [0.3.0] - Sports Display
- ESPN API integration
- Multi-league support (NHL, NBA, NFL, MLB)
- Adaptive layouts (1-4 games)
- Live score updates

### [0.2.0] - BLE Communication
- Reverse-engineered BLE protocol
- Reliable packet transmission
- Connection management

### [0.1.0] - Initial Implementation
- Basic pixel-by-pixel rendering
- Single panel support
- Proof of concept

---

## Migration Guide

### Upgrading to 2.0.0 (Environment Variables)

1. **Create your config file:**
   ```bash
   cp config.env.example config.env
   ```

2. **Fill in your values** (replace the placeholders in `config.env`)

3. **Remove any hardcoded values** from your local modifications

4. **Run as normal:**
   ```bash
   python display_manager.py
   ```

That's it! The code will automatically load from `config.env`.

### Upgrading to 1.0.0 (Clean Codebase)

If you were using old pixel-by-pixel functions:

1. **Find your usage** of removed functions
2. **Replace with PNG rendering:**
   ```python
   # Old way
   await draw_pixels_batch(client, pixels)
   
   # New way
   img = render_scoreboard(games)  # or render_weather(), etc.
   await upload_png(client, img)
   ```

3. **Old functions still available** in `legacy/legacy_utils.py` if needed

---

## Breaking Changes

### 2.0.0
- ⚠️ Hardcoded config in code no longer works
- ✅ Solution: Use `config.env` or system environment variables

### 1.0.0
- ⚠️ Pixel-by-pixel functions removed from `panel_core.py`
- ✅ Solution: Use PNG rendering or import from `legacy/legacy_utils.py`
- ⚠️ Bulk text functions removed
- ✅ Solution: Use PNG rendering instead (much better!)

---

## Future Plans

- [ ] Docker container support
- [ ] Web UI for configuration
- [ ] More clock themes
- [ ] Support for more LED panel types
- [ ] Plugin system for custom displays
- [ ] Mobile app for remote control

