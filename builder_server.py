"""
Builder API server for the LED panel layout builder.

Serves template management and preview rendering endpoints for the React builder UI.
Runs independently of the emulator — no physical or virtual display required.

Usage:
    python builder_server.py [--port 8081] [--host localhost]

The React builder dev server (cd builder && npm start) proxies API calls here.
"""
import argparse
import asyncio
import io
import logging
import traceback
from pathlib import Path

import yaml
from aiohttp import web

import logging_config

logger = logging.getLogger('led_panel.builder_server')

# Project root is the directory this file lives in
ROOT = Path(__file__).parent


# ---------------------------------------------------------------------------
# CORS middleware — required so React dev server (port 3000) can call port 8081
# ---------------------------------------------------------------------------

CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
}


@web.middleware
async def cors_middleware(request, handler):
    if request.method == 'OPTIONS':
        return web.Response(headers=CORS_HEADERS)
    response = await handler(request)
    response.headers.update(CORS_HEADERS)
    return response


# ---------------------------------------------------------------------------
# Template handlers
# ---------------------------------------------------------------------------

TEMPLATE_DIR = ROOT / 'core' / 'layout' / 'templates'


async def handle_list_templates(request):
    """List all available .yml template files."""
    try:
        if not TEMPLATE_DIR.exists():
            return web.json_response({'templates': []})

        templates = [
            {
                'name': f.name,
                'size': f.stat().st_size,
                'modified': f.stat().st_mtime,
            }
            for f in TEMPLATE_DIR.glob('*.yml')
        ]
        return web.json_response({'templates': sorted(templates, key=lambda x: x['name'])})
    except Exception as e:
        logger.error(f"Failed to list templates: {e}")
        return web.json_response({'templates': []})


async def handle_get_template(request):
    """Return a single template file as JSON."""
    try:
        filename = request.match_info['filename']
        template_file = TEMPLATE_DIR / filename

        if not template_file.exists() or not template_file.suffix == '.yml':
            return web.json_response({'error': 'Template not found'}, status=404)

        with open(template_file) as f:
            data = yaml.safe_load(f)

        return web.json_response(data)
    except Exception as e:
        logger.error(f"Failed to load template: {e}")
        return web.json_response({'error': str(e)}, status=500)


async def handle_save_template(request):
    """Save a template dict as a .yml file."""
    try:
        body = await request.json()
        filename = body.get('filename', 'custom_template.yml')
        template_data = body.get('template', {})

        if not filename.endswith('.yml'):
            filename += '.yml'

        TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
        template_file = TEMPLATE_DIR / filename

        with open(template_file, 'w') as f:
            yaml.dump(template_data, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Saved template: {filename}")
        return web.json_response({'success': True, 'filename': filename, 'path': str(template_file)})
    except Exception as e:
        logger.error(f"Failed to save template: {e}")
        return web.json_response({'success': False, 'error': str(e)}, status=500)


# ---------------------------------------------------------------------------
# Sample / live data handlers
# ---------------------------------------------------------------------------

async def handle_get_sports_data(request):
    """Return sports data for preview (live if available, else sample)."""
    sample = [
        {'home': 'DET', 'away': 'BOS', 'home_score': 95, 'away_score': 102,
         'clock': '2:45', 'period': 'Q4', 'league': 'NBA', 'state': 'inProgress'},
        {'home': 'LAL', 'away': 'GSW', 'home_score': 88, 'away_score': 91,
         'clock': '5:12', 'period': 'Q3', 'league': 'NBA', 'state': 'inProgress'},
    ]
    try:
        from core.data import sports_fetcher
        games = await sports_fetcher.fetch_games(filter_teams=True)
        if games:
            return web.json_response({'games': games[:4]})
    except Exception as e:
        logger.debug(f"Using sample sports data: {e}")
    return web.json_response({'games': sample})


async def handle_get_stocks_data(request):
    """Return stocks data for preview (live if available, else sample)."""
    sample = [
        {'symbol': 'AAPL', 'price': 195.50, 'change_percent': 2.3, 'is_up': True},
        {'symbol': 'TSLA', 'price': 245.10, 'change_percent': -1.2, 'is_up': False},
        {'symbol': 'GOOGL', 'price': 142.75, 'change_percent': 0.8, 'is_up': True},
        {'symbol': 'MSFT', 'price': 378.90, 'change_percent': 1.5, 'is_up': True},
    ]
    try:
        from core.data import stocks_fetcher
        quotes = await stocks_fetcher.get_cached_or_fetch()
        if quotes:
            return web.json_response({'quotes': quotes[:4]})
    except Exception as e:
        logger.debug(f"Using sample stocks data: {e}")
    return web.json_response({'quotes': sample})


async def handle_get_weather_data(request):
    """Return weather data for preview (live if available, else sample)."""
    sample = {
        'temp': 45, 'feels_like': 42, 'temp_max': 50, 'temp_min': 38,
        'condition': 'clouds', 'description': 'Cloudy', 'zipcode': '44444',
        'humidity': 65, 'wind_speed': 10,
    }
    try:
        from core.data import weather_fetcher
        weather = await weather_fetcher.get_cached_or_fetch()
        if weather:
            return web.json_response({'weather': weather})
    except Exception as e:
        logger.debug(f"Using sample weather data: {e}")
    return web.json_response({'weather': sample})


# ---------------------------------------------------------------------------
# Preview render handler
# ---------------------------------------------------------------------------

def _render_weather_forecast_preview(
    template_dict: dict,
    scenario: str,
    width: int,
    height: int,
    forecasts: list,
) -> "Image.Image":
    """
    Render a weather forecast scenario directly from the builder template dict.

    The element-builder's 'two_items' weather scenario stores forecast elements
    (forecast_icon, forecast_temp, forecast_time, high_temp, low_temp) in an
    item_template that repeats with a y-offset per item.  This helper renders
    sample forecast data using that template without going through LayoutTemplate
    so no schema mismatch occurs.
    """
    from PIL import Image as PILImage, ImageDraw, ImageFont

    img = PILImage.new('RGB', (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(img)

    scenario_data = template_dict.get(scenario, {})
    item_height = scenario_data.get('item_height', height // max(len(forecasts), 1))
    item_template = scenario_data.get('item_template', {})

    if not item_template:
        font = _load_preview_font(9)
        draw.text((2, 5), "No forecast elements yet", fill=(255, 255, 0), font=font)
        draw.text((2, 15), "Add elements from the palette", fill=(150, 150, 150), font=font)
        return img

    n_items = {'two_items': 2, 'three_items': 3, 'four_items': 4}.get(scenario, 2)

    for idx, forecast in enumerate(forecasts[:n_items]):
        y_off = idx * item_height

        for elem_name, spec in item_template.items():
            if elem_name in ('weather_icon', 'forecast_icon'):
                try:
                    from core.data.weather_data import load_weather_icon
                    w = spec.get('width', 12)
                    h_sz = spec.get('height', 12)
                    icon = load_weather_icon(forecast.get('condition', 'clear'), size=(w, h_sz))
                    if icon:
                        ix = spec.get('x', 0)
                        iy = spec.get('y', 0) + y_off
                        img.paste(icon, (ix, iy), icon if icon.mode == 'RGBA' else None)
                except Exception:
                    pass
                continue

            # Determine display text for each element type
            high = forecast.get('high', '--')
            low = forecast.get('low', '--')
            day = forecast.get('day', f'D{idx + 1}')
            cond = forecast.get('condition', 'clear')

            if 'high_temp' in elem_name or (elem_name == 'forecast_temp' and 'low' not in elem_name):
                text = f"{int(high)}°" if isinstance(high, (int, float)) else '--'
            elif 'low_temp' in elem_name:
                text = f"{int(low)}°" if isinstance(low, (int, float)) else '--'
            elif 'forecast_temp' in elem_name:
                text = f"{int(high)}°" if isinstance(high, (int, float)) else '--'
            elif 'time' in elem_name or 'day' in elem_name:
                text = day
            elif 'condition' in elem_name:
                text = cond[:4].upper()
            else:
                text = elem_name[:5]

            font_size = spec.get('font_size', 8)
            color = _resolve_preview_color(spec.get('color', 'white'))
            font = _load_preview_font(font_size)
            x = spec.get('x', 0)
            y = spec.get('y', 0) + y_off

            align = spec.get('align', 'left')
            if align in ('center', 'right'):
                try:
                    bbox = font.getbbox(text)
                    tw = bbox[2] - bbox[0]
                    x = x - (tw // 2 if align == 'center' else tw)
                except Exception:
                    pass

            draw.text((x, y), text, fill=color, font=font)

    return img


def _load_preview_font(size: int):
    """Load PixelOperator font or fall back to PIL default."""
    from PIL import ImageFont
    try:
        return ImageFont.truetype('./fonts/PixelOperator.ttf', size)
    except OSError:
        return ImageFont.load_default()


def _resolve_preview_color(color_name: str):
    """Resolve a color name or hex string to an RGB tuple."""
    if isinstance(color_name, (list, tuple)) and len(color_name) == 3:
        return tuple(color_name)
    if isinstance(color_name, str) and color_name.startswith('#') and len(color_name) == 7:
        return (int(color_name[1:3], 16), int(color_name[3:5], 16), int(color_name[5:7], 16))
    return {
        'white': (255, 255, 255), 'gray': (150, 150, 150), 'red': (255, 0, 0),
        'green': (0, 255, 0), 'blue': (0, 0, 255), 'yellow': (255, 255, 0),
        'cyan': (0, 255, 255), 'orange': (255, 165, 0), 'magenta': (255, 0, 255),
        'temp_color': (255, 255, 0),
    }.get(color_name, (255, 255, 255))


async def handle_render_preview(request):
    """Render a template to a PNG using the actual Python renderer."""
    try:
        from core.layout import LayoutTemplate
        from core.rendering.templated_renderer import (
            TemplatedSportsRenderer,
            TemplatedStocksRenderer,
            TemplatedWeatherRenderer,
        )

        body = await request.json()
        mode = body.get('mode', 'sports')
        template_dict = body.get('template', {})
        scenario = body.get('scenario', 'one_item')

        if mode == 'sports':
            sample_data = [
                {'home': 'DET', 'away': 'BOS', 'home_score': 95, 'away_score': 102,
                 'clock': '2:45', 'period': 'Q4', 'league': 'NBA', 'state': 'inProgress'},
                {'home': 'LAL', 'away': 'GSW', 'home_score': 88, 'away_score': 91,
                 'clock': '5:12', 'period': 'Q3', 'league': 'NBA', 'state': 'inProgress'},
                {'home': 'NYK', 'away': 'MIA', 'home_score': 76, 'away_score': 82,
                 'clock': '0:45', 'period': 'Q4', 'league': 'NBA', 'state': 'inProgress'},
                {'home': 'PHI', 'away': 'CHI', 'home_score': 103, 'away_score': 98,
                 'clock': '8:30', 'period': 'Q2', 'league': 'NBA', 'state': 'inProgress'},
            ]
        elif mode == 'stocks':
            sample_data = [
                {'symbol': 'AAPL', 'price': 195.50, 'change_percent': 2.3, 'is_up': True},
                {'symbol': 'TSLA', 'price': 245.10, 'change_percent': -1.2, 'is_up': False},
                {'symbol': 'GOOGL', 'price': 142.75, 'change_percent': 0.8, 'is_up': True},
                {'symbol': 'MSFT', 'price': 378.90, 'change_percent': 1.5, 'is_up': True},
            ]
        else:
            sample_data = {
                'temp': 45, 'feels_like': 42, 'temp_max': 50, 'temp_min': 38,
                'condition': 'clouds', 'description': 'Cloudy', 'zipcode': '44444',
                'humidity': 65, 'wind_speed': 10,
            }

        width = template_dict.get('canvas_width', 64)
        height = template_dict.get('canvas_height', 20)

        if mode == 'sports':
            template = LayoutTemplate.from_dict(mode, template_dict, width, height)
            renderer = TemplatedSportsRenderer(template)
            n = {'one_item': 1, 'two_items': 2, 'three_items': 3, 'four_items': 4}.get(scenario, 1)
            image = renderer.render_games(sample_data[:n], display_type='live')
        elif mode == 'stocks':
            template = LayoutTemplate.from_dict(mode, template_dict, width, height)
            renderer = TemplatedStocksRenderer(template)
            n = {'one_item': 1, 'two_items': 2, 'four_items': 4}.get(scenario, 1)
            image = renderer.render_stocks(sample_data[:n])
        else:  # weather
            if scenario == 'one_item':
                template = LayoutTemplate.from_dict(mode, template_dict, width, height)
                renderer = TemplatedWeatherRenderer(template)
                image = renderer.render_weather(sample_data)
            else:
                # Forecast scenario — render repeating items with sample days
                sample_forecasts = [
                    {'day': 'Mon', 'condition': 'clear',  'high': 52, 'low': 38},
                    {'day': 'Tue', 'condition': 'rain',   'high': 45, 'low': 33},
                    {'day': 'Wed', 'condition': 'snow',   'high': 32, 'low': 25},
                    {'day': 'Thu', 'condition': 'clouds', 'high': 48, 'low': 36},
                ]
                image = _render_weather_forecast_preview(
                    template_dict, scenario, width, height, sample_forecasts
                )

        buf = io.BytesIO()
        image.save(buf, format='PNG')
        buf.seek(0)
        return web.Response(body=buf.getvalue(), content_type='image/png')

    except Exception as e:
        logger.error(f"Preview render failed: {e}")
        traceback.print_exc()
        return web.json_response(
            {'error': str(e), 'traceback': traceback.format_exc()},
            status=500,
        )


# ---------------------------------------------------------------------------
# Composite template handlers
# ---------------------------------------------------------------------------

COMPOSITE_TEMPLATE_DIR = ROOT / 'templates'


async def handle_list_composite_templates(request):
    """List all composite template .yml files in templates/."""
    try:
        if not COMPOSITE_TEMPLATE_DIR.exists():
            return web.json_response({'templates': []})
        templates = [
            {'name': f.name, 'size': f.stat().st_size, 'modified': f.stat().st_mtime}
            for f in sorted(COMPOSITE_TEMPLATE_DIR.glob('*.yml'))
        ]
        return web.json_response({'templates': templates})
    except Exception as e:
        logger.error(f"Failed to list composite templates: {e}")
        return web.json_response({'templates': []})


async def handle_get_composite_template(request):
    """Return a composite template file as JSON."""
    try:
        filename = request.match_info['filename']
        if not filename.endswith('.yml'):
            filename += '.yml'
        template_file = COMPOSITE_TEMPLATE_DIR / filename
        if not template_file.exists():
            return web.json_response({'error': 'Template not found'}, status=404)
        with open(template_file) as f:
            data = yaml.safe_load(f)
        return web.json_response(data)
    except Exception as e:
        logger.error(f"Failed to load composite template: {e}")
        return web.json_response({'error': str(e)}, status=500)


async def handle_save_composite_template(request):
    """Save raw YAML content as a composite template file."""
    try:
        body = await request.json()
        filename = body.get('filename', 'template.yml')
        content = body.get('content', '')
        if not filename.endswith('.yml'):
            filename += '.yml'
        COMPOSITE_TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
        template_file = COMPOSITE_TEMPLATE_DIR / filename
        with open(template_file, 'w') as f:
            f.write(content)
        logger.info(f"Saved composite template: {filename}")
        return web.json_response({'success': True, 'filename': filename})
    except Exception as e:
        logger.error(f"Failed to save composite template: {e}")
        return web.json_response({'success': False, 'error': str(e)}, status=500)


async def handle_composite_preview(request):
    """Render a composite template config to PNG using CompositeRenderer."""
    try:
        from core.components import registry
        from core.components.composite_renderer import CompositeRenderer

        body = await request.json()
        template_config = body.get('template', {})

        renderer = CompositeRenderer(template_config, registry)
        image = await renderer.render()

        buf = io.BytesIO()
        image.save(buf, format='PNG')
        buf.seek(0)
        return web.Response(body=buf.getvalue(), content_type='image/png')
    except Exception as e:
        logger.error(f"Composite preview failed: {e}")
        traceback.print_exc()
        return web.json_response(
            {'error': str(e), 'traceback': traceback.format_exc()},
            status=500,
        )


# ---------------------------------------------------------------------------
# Config template handlers
# ---------------------------------------------------------------------------

async def handle_get_config_template(request):
    """Return the layout_templates section and display config from config.yml."""
    try:
        from config import get_all_config
        cfg = get_all_config()

        layout_templates = cfg.get('layout_templates', {})
        display_config = cfg.get('display', {})
        ipixel = display_config.get('ipixel', {})

        panel_width = ipixel.get('size_width', 64)
        panel_height = ipixel.get('size_height', 20)
        num_panels = len(ipixel.get('ble_addresses') or []) or 2

        if not layout_templates:
            return web.json_response({
                'has_templates': False,
                'message': 'No layout_templates section in config.yml',
                'display': {'panel_width': panel_width, 'panel_height': panel_height, 'num_panels': num_panels},
            })

        orientation = 'horizontal'
        first_mode = next((m for m in ('sports', 'stocks', 'weather') if m in layout_templates), None)
        if first_mode:
            cw = layout_templates[first_mode].get('canvas_width')
            ch = layout_templates[first_mode].get('canvas_height')
            if cw and ch:
                if cw == panel_width * num_panels and ch == panel_height:
                    orientation = 'horizontal'
                elif ch == panel_height * num_panels and cw == panel_width:
                    orientation = 'vertical'

        return web.json_response({
            'has_templates': True,
            'templates': layout_templates,
            'display': {
                'panel_width': panel_width,
                'panel_height': panel_height,
                'num_panels': num_panels,
                'orientation': orientation,
                'adapter': display_config.get('adapter', 'ipixel'),
            },
        })
    except Exception as e:
        logger.error(f"Failed to load config templates: {e}")
        return web.json_response({'has_templates': False, 'error': str(e)}, status=500)


async def handle_save_to_config(request):
    """Return generated YAML for the user to paste into config.yml."""
    try:
        body = await request.json()
        template_yaml = body.get('template_yaml', '')

        if not template_yaml:
            return web.json_response({'success': False, 'error': 'No template data provided'}, status=400)

        config_path = ROOT / 'config.yml'
        if not config_path.exists():
            return web.json_response({'success': False, 'error': 'config.yml not found'}, status=404)

        with open(config_path) as f:
            config_content = f.read()

        if 'layout_templates:' in config_content:
            msg = 'Template generated. Replace the layout_templates section in config.yml with the YAML below.'
        else:
            msg = 'Template generated. Add the YAML below to the end of config.yml.'

        return web.json_response({
            'success': True,
            'message': msg,
            'yaml': template_yaml,
            'manual_update': True,
        })
    except Exception as e:
        logger.error(f"Save to config failed: {e}")
        return web.json_response({'success': False, 'error': str(e)}, status=500)


# ---------------------------------------------------------------------------
# App factory and entry point
# ---------------------------------------------------------------------------

def create_app() -> web.Application:
    app = web.Application(middlewares=[cors_middleware])
    app.router.add_get('/templates', handle_list_templates)
    app.router.add_get('/templates/{filename}', handle_get_template)
    app.router.add_post('/templates', handle_save_template)
    app.router.add_get('/api/sports', handle_get_sports_data)
    app.router.add_get('/api/stocks', handle_get_stocks_data)
    app.router.add_get('/api/weather', handle_get_weather_data)
    app.router.add_post('/api/preview', handle_render_preview)
    app.router.add_get('/api/config_template', handle_get_config_template)
    app.router.add_post('/api/save_to_config', handle_save_to_config)
    app.router.add_get('/api/composite_templates', handle_list_composite_templates)
    app.router.add_get('/api/composite_templates/{filename}', handle_get_composite_template)
    app.router.add_post('/api/composite_templates', handle_save_composite_template)
    app.router.add_post('/api/composite_preview', handle_composite_preview)
    return app


async def main(host: str = 'localhost', port: int = 8081) -> None:
    app = create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, host, port).start()
    logger.info(f"Builder API server running at http://{host}:{port}")
    await asyncio.Event().wait()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='LED Panel Layout Builder API server')
    parser.add_argument('--port', type=int, default=8081, help='API server port (default: 8081)')
    parser.add_argument('--host', default='localhost', help='API server host (default: localhost)')
    args = parser.parse_args()
    try:
        asyncio.run(main(args.host, args.port))
    except KeyboardInterrupt:
        pass
