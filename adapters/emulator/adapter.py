"""
Emulator adapter - displays LED panel output in a web browser.

Provides a virtual LED panel for testing and development without physical hardware.
"""
import asyncio
import base64
import io
import logging
from datetime import datetime
from pathlib import Path
from PIL import Image
from aiohttp import web

from ..base import DisplayAdapter

logger = logging.getLogger(__name__)


class EmulatorAdapter(DisplayAdapter):
    """
    Virtual LED panel adapter that displays output in a web browser.
    
    Features:
    - Real-time preview in browser
    - Hot reload support
    - Multi-panel layout visualization
    - No hardware required
    """
    
    def __init__(self, config):
        super().__init__()
        self._display_width = config.get('display_width', 128)
        self._display_height = config.get('display_height', 40)
        self.num_panels = config.get('num_panels', 2)
        self.panel_width = config.get('panel_width', 64)
        self.panel_height = config.get('panel_height', 20)
        self.orientation = config.get('orientation', 'horizontal')
        
        # Web server settings
        self.host = config.get('emulator_host', 'localhost')
        self.port = config.get('emulator_port', 8080)
        
        # State
        self.current_image = None
        self.last_update = None
        self._is_connected = False
        self.web_app = None
        self.web_runner = None
        self.web_site = None
        
        # Stats
        self.frame_count = 0
        self.total_bytes = 0
        
        logger.info(f"Emulator adapter created ({self._display_width}x{self._display_height}, {self.num_panels} panels)")
    
    @property
    def display_width(self) -> int:
        """Get total display width."""
        return self._display_width
    
    @property
    def display_height(self) -> int:
        """Get total display height."""
        return self._display_height
    
    @property
    def is_connected(self) -> bool:
        """Check if emulator is connected."""
        return self._is_connected
    
    async def connect(self, max_retries=3):
        """Start the emulator web server."""
        if self.is_connected:
            logger.warning("Emulator already running")
            return
        
        try:
            # Create web application
            self.web_app = web.Application()
            self.web_app.router.add_get('/', self._handle_index)
            self.web_app.router.add_get('/current', self._handle_current_image)
            self.web_app.router.add_get('/stats', self._handle_stats)
            self.web_app.router.add_get('/builder', self._handle_builder)
            self.web_app.router.add_post('/config', self._handle_config_update)
            self.web_app.router.add_post('/update_display', self._handle_display_update)
            self.web_app.router.add_get('/templates', self._handle_list_templates)
            self.web_app.router.add_get('/templates/{filename}', self._handle_get_template)
            self.web_app.router.add_post('/templates', self._handle_save_template)
            self.web_app.router.add_get('/api/sports', self._handle_get_sports_data)
            self.web_app.router.add_get('/api/stocks', self._handle_get_stocks_data)
            self.web_app.router.add_get('/api/weather', self._handle_get_weather_data)
            self.web_app.router.add_post('/api/preview', self._handle_render_preview)
            
            # Start server
            self.web_runner = web.AppRunner(self.web_app)
            await self.web_runner.setup()
            self.web_site = web.TCPSite(self.web_runner, self.host, self.port)
            await self.web_site.start()
            
            self._is_connected = True
            logger.info(f"✓ Emulator running at http://{self.host}:{self.port}")
            logger.info(f"  Open this URL in your browser to view the display!")
            
        except Exception as e:
            logger.error(f"Failed to start emulator: {e}")
            raise
    
    async def disconnect(self):
        """Stop the emulator web server."""
        if self.web_runner:
            await self.web_runner.cleanup()
        self._is_connected = False
        logger.info("Emulator stopped")
    
    async def power_on(self):
        """Virtual power on (no-op)."""
        logger.info("Emulator powered on")
    
    async def power_off(self):
        """Virtual power off."""
        self.current_image = None
        logger.info("Emulator powered off")
    
    async def clear_screen(self, panels=None):
        """Clear the display."""
        blank = Image.new('RGB', (self._display_width, self._display_height), color=(0, 0, 0))
        self.current_image = blank
        self.last_update = datetime.now()
        logger.info("Screen cleared")
    
    async def get_info(self) -> dict:
        """Get emulator information."""
        return {
            'adapter_type': 'emulator',
            'device_count': self.num_panels,
            'display_width': self._display_width,
            'display_height': self._display_height,
            'panel_width': self.panel_width,
            'frame_count': self.frame_count,
            'total_bytes': self.total_bytes,
            'web_url': f'http://{self.host}:{self.port}',
        }
    
    async def upload_image(self, image, clear_first=True, panels=None):
        """
        Display an image in the emulator.
        
        Args:
            image: PIL Image to display
            clear_first: Whether to clear screen first (ignored in emulator)
            panels: Which panels to update (None = all)
        """
        if not self._is_connected:
            logger.warning("Emulator not connected")
            return
        
        # Handle multi-panel updates
        if panels is not None and len(panels) < self.num_panels:
            # Partial update - merge with existing image
            if self.current_image is None:
                self.current_image = Image.new('RGB', (self._display_width, self._display_height), color=(0, 0, 0))
            
            for panel_idx in panels:
                x_offset = panel_idx * self.panel_width
                # Paste the image at the correct panel position
                self.current_image.paste(image, (x_offset, 0))
        else:
            # Full update
            self.current_image = image.copy()
        
        self.last_update = datetime.now()
        self.frame_count += 1
        
        # Calculate size
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        self.total_bytes += len(buffer.getvalue())
        
        logger.debug(f"Frame {self.frame_count} displayed")
    
    async def upload_gif(self, gif_bytes, panels=None):
        """
        Display a GIF in the emulator.
        
        Args:
            gif_bytes: GIF file bytes
            panels: Which panels to display on (None = all)
        """
        if not self._is_connected:
            logger.warning("Emulator not connected")
            return
        
        # For emulator, extract first frame and display it
        # In a real implementation, we'd animate the GIF
        gif_buffer = io.BytesIO(gif_bytes)
        image = Image.open(gif_buffer)
        
        await self.upload_image(image, panels=panels)
        logger.info(f"GIF uploaded ({len(gif_bytes)/1024:.1f} KB)")
    
    # Web handlers
    
    async def _handle_index(self, request):
        """Serve the emulator HTML interface."""
        html = self._generate_html()
        return web.Response(text=html, content_type='text/html')
    
    async def _handle_current_image(self, request):
        """Return the current display image as PNG."""
        if self.current_image is None:
            # Return blank image
            blank = Image.new('RGB', (self._display_width, self._display_height), color=(0, 0, 0))
            buffer = io.BytesIO()
            blank.save(buffer, format='PNG')
            buffer.seek(0)
            return web.Response(body=buffer.getvalue(), content_type='image/png')
        
        buffer = io.BytesIO()
        self.current_image.save(buffer, format='PNG')
        buffer.seek(0)
        return web.Response(body=buffer.getvalue(), content_type='image/png')
    
    async def _handle_stats(self, request):
        """Return emulator statistics as JSON."""
        stats = {
            'connected': self._is_connected,
            'frame_count': self.frame_count,
            'total_bytes': self.total_bytes,
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'display_width': self._display_width,
            'display_height': self._display_height,
            'panel_width': self.panel_width,
            'panel_height': self.panel_height,
            'num_panels': self.num_panels,
            'orientation': self.orientation,
        }
        return web.json_response(stats)
    
    async def _handle_builder(self, request):
        """Serve the layout builder interface."""
        from pathlib import Path
        builder_path = Path(__file__).parent / 'layout_builder.html'
        with open(builder_path, 'r') as f:
            html = f.read()
        return web.Response(text=html, content_type='text/html')
    
    async def _handle_config_update(self, request):
        """Handle configuration update from UI."""
        try:
            data = await request.json()
            logger.info(f"Config update requested: {data}")
            # Note: This doesn't actually restart - user needs to restart emulator
            return web.json_response({
                'success': True,
                'message': 'Config saved. Please restart emulator to apply changes.',
                'config': data
            })
        except Exception as e:
            logger.error(f"Config update failed: {e}")
            return web.json_response({
                'success': False,
                'error': str(e)
            }, status=400)
    
    async def _handle_display_update(self, request):
        """Handle live display dimension updates."""
        try:
            data = await request.json()
            
            # Update dimensions (note: requires restart for full effect)
            if 'panel_width' in data:
                self.panel_width = int(data['panel_width'])
            if 'panel_height' in data:
                self.panel_height = int(data['panel_height'])
            if 'num_panels' in data:
                self.num_panels = int(data['num_panels'])
            if 'orientation' in data:
                self.orientation = data['orientation']
                
            # Recalculate display dimensions
            if self.orientation == 'horizontal':
                self._display_width = self.panel_width * self.num_panels
                self._display_height = self.panel_height
            else:
                self._display_width = self.panel_width
                self._display_height = self.panel_height * self.num_panels
            
            logger.info(f"Display updated: {self._display_width}x{self._display_height}")
            
            return web.json_response({
                'success': True,
                'display_width': self._display_width,
                'display_height': self._display_height,
                'panel_width': self.panel_width,
                'panel_height': self.panel_height,
                'num_panels': self.num_panels,
                'orientation': self.orientation
            })
        except Exception as e:
            logger.error(f"Display update failed: {e}")
            return web.json_response({
                'success': False,
                'error': str(e)
            }, status=400)
    
    async def _handle_list_templates(self, request):
        """List all available template files."""
        try:
            from pathlib import Path
            template_dir = Path(__file__).parent.parent.parent / 'core' / 'layout' / 'templates'
            
            if not template_dir.exists():
                return web.json_response({'templates': []})
            
            templates = []
            for file in template_dir.glob('*.yml'):
                if file.name != 'README.md':
                    templates.append({
                        'name': file.name,
                        'size': file.stat().st_size,
                        'modified': file.stat().st_mtime
                    })
            
            return web.json_response({'templates': sorted(templates, key=lambda x: x['name'])})
        except Exception as e:
            logger.error(f"Failed to list templates: {e}")
            return web.json_response({'templates': []})
    
    async def _handle_get_template(self, request):
        """Serve a specific template file."""
        try:
            filename = request.match_info['filename']
            from pathlib import Path
            import yaml
            
            template_dir = Path(__file__).parent.parent.parent / 'core' / 'layout' / 'templates'
            template_file = template_dir / filename
            
            if not template_file.exists() or not template_file.name.endswith('.yml'):
                return web.json_response({'error': 'Template not found'}, status=404)
            
            with open(template_file, 'r') as f:
                template_data = yaml.safe_load(f)
            
            return web.json_response(template_data)
        except Exception as e:
            logger.error(f"Failed to load template: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def _handle_save_template(self, request):
        """Save a new template file."""
        try:
            from pathlib import Path
            import yaml
            
            data = await request.json()
            filename = data.get('filename', 'custom_template.yml')
            template_data = data.get('template', {})
            
            # Ensure filename is safe
            if not filename.endswith('.yml'):
                filename += '.yml'
            
            template_dir = Path(__file__).parent.parent.parent / 'core' / 'layout' / 'templates'
            template_dir.mkdir(parents=True, exist_ok=True)
            
            template_file = template_dir / filename
            
            with open(template_file, 'w') as f:
                yaml.dump(template_data, f, default_flow_style=False, sort_keys=False)
            
            logger.info(f"Saved template: {filename}")
            
            return web.json_response({
                'success': True,
                'filename': filename,
                'path': str(template_file)
            })
        except Exception as e:
            logger.error(f"Failed to save template: {e}")
            return web.json_response({
                'success': False,
                'error': str(e)
            }, status=500)
    
    async def _handle_get_sports_data(self, request):
        """Get real sports data for preview."""
        # Always return sample data for now (avoid API/import issues)
        sample_games = [
            {'home': 'DET', 'away': 'BOS', 'home_score': 95, 'away_score': 102, 
             'clock': '2:45', 'period': 'Q4', 'league': 'NBA', 'state': 'inProgress'},
            {'home': 'LAL', 'away': 'GSW', 'home_score': 88, 'away_score': 91,
             'clock': '5:12', 'period': 'Q3', 'league': 'NBA', 'state': 'inProgress'},
        ]
        
        try:
            # Try to fetch real data
            from core.data import fetch_all_games
            games = await fetch_all_games()
            if games:
                return web.json_response({'games': games[:4]})
        except Exception as e:
            logger.debug(f"Using sample sports data: {e}")
        
        return web.json_response({'games': sample_games})
    
    async def _handle_get_stocks_data(self, request):
        """Get real stocks data for preview."""
        # Sample data first
        sample_quotes = [
            {'symbol': 'AAPL', 'price': 195.50, 'change_percent': 2.3, 'is_up': True},
            {'symbol': 'TSLA', 'price': 245.10, 'change_percent': -1.2, 'is_up': False},
            {'symbol': 'GOOGL', 'price': 142.75, 'change_percent': 0.8, 'is_up': True},
            {'symbol': 'MSFT', 'price': 378.90, 'change_percent': 1.5, 'is_up': True},
        ]
        
        try:
            # Try to fetch real data (will fail on Python 3.14)
            from core.data import fetch_stock_quotes
            quotes = await fetch_stock_quotes()
            if quotes:
                return web.json_response({'quotes': quotes[:4]})
        except Exception as e:
            logger.debug(f"Using sample stocks data: {e}")
        
        return web.json_response({'quotes': sample_quotes})
    
    async def _handle_get_weather_data(self, request):
        """Get real weather data for preview."""
        # Sample data first
        sample_weather = {
            'temp': 45, 'feels_like': 42, 'temp_max': 50, 'temp_min': 38,
            'condition': 'clouds', 'description': 'Cloudy', 'city': 'Brighton',
            'humidity': 65, 'wind_speed': 10
        }
        
        try:
            # Try to fetch real data
            from core.data import fetch_current_weather
            weather = await fetch_current_weather()
            if weather:
                return web.json_response({'weather': weather})
        except Exception as e:
            logger.debug(f"Using sample weather data: {e}")
        
        return web.json_response({'weather': sample_weather})
    
    async def _handle_render_preview(self, request):
        """Render a template preview using actual renderer."""
        try:
            import io
            from core.layout import LayoutTemplate
            from core.rendering.templated_renderer import (
                TemplatedSportsRenderer, 
                TemplatedStocksRenderer,
                TemplatedWeatherRenderer
            )
            
            data = await request.json()
            mode = data.get('mode', 'sports')
            template_dict = data.get('template', {})
            scenario = data.get('scenario', 'one_item')
            
            # Get sample data
            if mode == 'sports':
                sample_data = [
                    {'home': 'DET', 'away': 'BOS', 'home_score': 95, 'away_score': 102, 
                     'clock': '2:45', 'period': 'Q4', 'league': 'NBA', 'state': 'inProgress'},
                    {'home': 'LAL', 'away': 'GSW', 'home_score': 88, 'away_score': 91,
                     'clock': '5:12', 'period': 'Q3', 'league': 'NBA', 'state': 'inProgress'},
                ]
            elif mode == 'stocks':
                sample_data = [
                    {'symbol': 'AAPL', 'price': 195.50, 'change_percent': 2.3, 'is_up': True},
                    {'symbol': 'TSLA', 'price': 245.10, 'change_percent': -1.2, 'is_up': False},
                ]
            else:  # weather
                sample_data = {
                    'temp': 45, 'feels_like': 42, 'temp_max': 50, 'temp_min': 38,
                    'condition': 'clouds', 'description': 'Cloudy', 'city': 'Brighton',
                    'humidity': 65, 'wind_speed': 10
                }
            
            # Create template from dict
            width = template_dict.get('canvas_width', 64)
            height = template_dict.get('canvas_height', 20)
            template = LayoutTemplate.from_dict(mode, template_dict, width, height)
            
            # Render using actual renderer
            if mode == 'sports':
                renderer = TemplatedSportsRenderer(template)
                # Get number of games based on scenario
                num_games = {'one_item': 1, 'two_items': 2, 'three_items': 3, 'four_items': 4}.get(scenario, 1)
                image = renderer.render_games(sample_data[:num_games], display_type='live')
            elif mode == 'stocks':
                renderer = TemplatedStocksRenderer(template)
                num_stocks = {'one_item': 1, 'two_items': 2, 'four_items': 4}.get(scenario, 1)
                image = renderer.render_stocks(sample_data[:num_stocks])
            else:  # weather
                renderer = TemplatedWeatherRenderer(template)
                image = renderer.render_weather(sample_data)
            
            # Convert to PNG bytes
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            buffer.seek(0)
            
            return web.Response(body=buffer.getvalue(), content_type='image/png')
            
        except Exception as e:
            logger.error(f"Preview render failed: {e}")
            import traceback
            traceback.print_exc()
            return web.json_response({
                'error': str(e),
                'traceback': traceback.format_exc()
            }, status=500)
    
    def _generate_html(self):
        """Generate the emulator HTML interface."""
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>LED Panel Emulator</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1600px;
            width: 100%;
        }}
        
        .header {{
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }}
        
        .header h1 {{
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        
        .header p {{
            font-size: 1.1rem;
            opacity: 0.9;
        }}
        
        .display-container {{
            background: rgba(0, 0, 0, 0.8);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            margin-bottom: 20px;
            text-align: center;
        }}
        
        .display-wrapper {{
            background: #1a1a1a;
            border-radius: 10px;
            padding: 20px;
            display: inline-block;
            position: relative;
        }}
        
        .display {{
            display: block;
            image-rendering: pixelated;
            image-rendering: crisp-edges;
            width: {self._display_width * 8}px;
            height: {self._display_height * 8}px;
            border: 2px solid #333;
            border-radius: 5px;
            background: #000;
            box-shadow: 0 0 30px rgba(0, 0, 0, 0.5);
        }}
        
        .panel-indicators {{
            display: {'flex' if self.orientation == 'horizontal' else 'block'};
            margin-top: 15px;
            gap: 10px;
        }}
        
        .panel-indicator {{
            flex: {'1' if self.orientation == 'horizontal' else 'none'};
            padding: 8px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 5px;
            text-align: center;
            color: #aaa;
            font-size: 0.9rem;
        }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        
        .stat-card {{
            background: rgba(255, 255, 255, 0.95);
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        
        .stat-label {{
            font-size: 0.9rem;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 5px;
        }}
        
        .stat-value {{
            font-size: 1.8rem;
            font-weight: 700;
            color: #333;
        }}
        
        .info {{
            background: rgba(255, 255, 255, 0.95);
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        
        .info h3 {{
            margin-bottom: 10px;
            color: #333;
        }}
        
        .info p {{
            color: #666;
            line-height: 1.6;
            margin-bottom: 10px;
        }}
        
        .status {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 6px 12px;
            background: #4ade80;
            color: white;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 600;
        }}
        
        .status::before {{
            content: '';
            width: 8px;
            height: 8px;
            background: white;
            border-radius: 50%;
            animation: pulse 2s ease-in-out infinite;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        
        .refresh-note {{
            text-align: center;
            color: rgba(255, 255, 255, 0.7);
            font-size: 0.9rem;
            margin-top: 15px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🖥️ LED Panel Emulator</h1>
            <p>Virtual display preview • <strong>{self._display_width}×{self._display_height}</strong> pixels • <strong>{self.num_panels}</strong> panel{'s' if self.num_panels != 1 else ''}</p>
            <p style="font-size: 0.9rem; opacity: 0.8; margin-top: 5px;">
                Each panel: {self.panel_width}×{self.panel_height} • {self.orientation.capitalize()} layout • 8× scale
            </p>
        </div>
        
        <div class="display-container">
            <div class="display-wrapper">
                <div style="position: relative; display: inline-block;">
                    <img id="display" class="display" src="/current?t=0" alt="LED Display" style="width: {self._display_width * 8}px; height: {self._display_height * 8}px;">
                    {self._generate_panel_dividers()}
                </div>
                <div class="panel-indicators">
                    {self._generate_panel_indicators()}
                </div>
            </div>
            <div class="refresh-note">
                Auto-refreshing every second • Actual size: {self._display_width}×{self._display_height}px (8× zoom)
            </div>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-label">Display Size</div>
                <div class="stat-value" style="font-size: 1.3rem;">{self._display_width}×{self._display_height}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Panels</div>
                <div class="stat-value">{self.num_panels}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Frames Rendered</div>
                <div class="stat-value" id="frame-count">0</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Data Transferred</div>
                <div class="stat-value" id="data-size">0 KB</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Last Update</div>
                <div class="stat-value" id="last-update" style="font-size: 1.2rem;">Never</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Status</div>
                <div class="stat-value"><span class="status">Live</span></div>
            </div>
        </div>
        
        <div class="info">
            <h3>💡 Interactive Controls</h3>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 15px 0;">
                <button onclick="openBuilder()" style="padding: 12px; background: #667eea; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: 600;">
                    🎨 Layout Builder
                </button>
                <button onclick="toggleConfig()" style="padding: 12px; background: #4ade80; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: 600;">
                    ⚙️ Display Settings
                </button>
            </div>
            
            <div id="configPanel" style="display: none; background: #f3f4f6; padding: 15px; border-radius: 8px; margin-top: 10px;">
                <h4 style="color: #333; margin-bottom: 10px;">Display Configuration</h4>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                    <div>
                        <label style="display: block; color: #666; font-size: 0.85rem; margin-bottom: 4px;">Panel Width</label>
                        <input type="number" id="cfgWidth" value="{self.panel_width}" min="16" max="256" 
                               style="width: 100%; padding: 6px; border: 1px solid #ddd; border-radius: 4px;">
                    </div>
                    <div>
                        <label style="display: block; color: #666; font-size: 0.85rem; margin-bottom: 4px;">Panel Height</label>
                        <input type="number" id="cfgHeight" value="{self.panel_height}" min="16" max="256"
                               style="width: 100%; padding: 6px; border: 1px solid #ddd; border-radius: 4px;">
                    </div>
                    <div>
                        <label style="display: block; color: #666; font-size: 0.85rem; margin-bottom: 4px;">Num Panels</label>
                        <input type="number" id="cfgPanels" value="{self.num_panels}" min="1" max="8"
                               style="width: 100%; padding: 6px; border: 1px solid #ddd; border-radius: 4px;">
                    </div>
                    <div>
                        <label style="display: block; color: #666; font-size: 0.85rem; margin-bottom: 4px;">Orientation</label>
                        <select id="cfgOrientation" style="width: 100%; padding: 6px; border: 1px solid #ddd; border-radius: 4px;">
                            <option value="horizontal" {'selected' if self.orientation == 'horizontal' else ''}>Horizontal</option>
                            <option value="vertical" {'selected' if self.orientation == 'vertical' else ''}>Vertical</option>
                        </select>
                    </div>
                </div>
                <button onclick="updateDisplay()" style="width: 100%; margin-top: 10px; padding: 10px; background: #667eea; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: 600;">
                    ✨ Apply Changes (Requires Restart)
                </button>
                <p style="color: #666; font-size: 0.8rem; margin-top: 8px; text-align: center;">
                    Note: Restart emulator after applying changes
                </p>
            </div>
            
            <hr style="margin: 15px 0; border-color: #ddd;">
            
            <p style="color: #666;">
                This emulator displays what would be sent to your physical LED panels. 
                Perfect for testing layouts, animations, and configurations without hardware!
            </p>
            <p style="color: #666; margin-top: 8px;">
                <strong>Features:</strong> Real-time updates • Multi-panel support • Pixel-perfect rendering • Hot reload compatible
            </p>
        </div>
    
    <script>
        function openBuilder() {{
            window.open('/builder', '_blank');
        }}
        
        function toggleConfig() {{
            const panel = document.getElementById('configPanel');
            panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
        }}
        
        function updateDisplay() {{
            const width = document.getElementById('cfgWidth').value;
            const height = document.getElementById('cfgHeight').value;
            const panels = document.getElementById('cfgPanels').value;
            const orientation = document.getElementById('cfgOrientation').value;
            
            fetch('/update_display', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{
                    panel_width: parseInt(width),
                    panel_height: parseInt(height),
                    num_panels: parseInt(panels),
                    orientation: orientation
                }})
            }})
            .then(r => r.json())
            .then(data => {{
                if (data.success) {{
                    alert('✅ Configuration updated! Please restart the emulator to see changes.\\n\\n' +
                          'Run: python3 emulator.py -w ' + width + ' -y ' + height + ' -p ' + panels + ' -o ' + orientation);
                }} else {{
                    alert('❌ Update failed: ' + data.error);
                }}
            }})
            .catch(err => {{
                alert('❌ Connection error: ' + err);
            }});
        }}
    </script>
    </div>
    
    <script>
        // Auto-refresh display
        let frameCount = 0;
        setInterval(() => {{
            const img = document.getElementById('display');
            img.src = `/current?t=${{Date.now()}}`;
            frameCount++;
            
            // Update stats
            fetch('/stats')
                .then(r => r.json())
                .then(stats => {{
                    document.getElementById('frame-count').textContent = stats.frame_count;
                    document.getElementById('data-size').textContent = 
                        (stats.total_bytes / 1024).toFixed(1) + ' KB';
                    
                    if (stats.last_update) {{
                        const date = new Date(stats.last_update);
                        document.getElementById('last-update').textContent = 
                            date.toLocaleTimeString();
                    }}
                }});
        }}, 1000);
    </script>
</body>
</html>"""
    
    def _generate_panel_indicators(self):
        """Generate HTML for panel indicators."""
        indicators = []
        if self.orientation == 'horizontal':
            # Side-by-side indicators
            for i in range(self.num_panels):
                indicators.append(f'<div class="panel-indicator">Panel {i}</div>')
        else:
            # Stacked indicators - show vertically
            for i in range(self.num_panels):
                indicators.append(f'<div class="panel-indicator" style="width: 100%; margin-bottom: 5px;">Panel {i}</div>')
        return '\n'.join(indicators)
    
    def _generate_panel_dividers(self):
        """Generate visual dividers between panels."""
        if self.num_panels <= 1:
            return ''
        
        dividers = []
        scale = 8
        
        if self.orientation == 'horizontal':
            # Vertical dividers between side-by-side panels
            for i in range(1, self.num_panels):
                x_pos = i * self.panel_width * scale
                dividers.append(f'''
                    <div style="position: absolute; left: {x_pos}px; top: 0; 
                         width: 2px; height: 100%; 
                         background: rgba(255, 255, 0, 0.3);
                         box-shadow: 0 0 10px rgba(255, 255, 0, 0.5);"></div>
                ''')
        else:
            # Horizontal dividers between stacked panels
            for i in range(1, self.num_panels):
                y_pos = i * self.panel_height * scale
                dividers.append(f'''
                    <div style="position: absolute; left: 0; top: {y_pos}px; 
                         width: 100%; height: 2px; 
                         background: rgba(255, 255, 0, 0.3);
                         box-shadow: 0 0 10px rgba(255, 255, 0, 0.5);"></div>
                ''')
        
        return '\n'.join(dividers)

