#!/usr/bin/env python3
"""
Test script for layout templates system.

Tests:
1. Layout template loading from config
2. Rendering with custom templates
3. Fallback to defaults when no custom template
4. Different panel configurations (64x64, 32x16, etc.)
"""
import asyncio
import logging
from PIL import Image

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_layout_loader():
    """Test layout template loading."""
    logger.info("=" * 60)
    logger.info("TEST 1: Layout Template Loader")
    logger.info("=" * 60)
    
    from core.layout import LayoutLoader
    
    # Test with empty config (should use defaults)
    loader = LayoutLoader({})
    
    # Get sports template
    sports_template = loader.get_template('sports')
    logger.info(f"✓ Loaded sports template: {sports_template.mode}")
    logger.info(f"  Canvas: {sports_template.canvas_width}×{sports_template.canvas_height}")
    logger.info(f"  Logo enabled: {sports_template.logo_enabled}")
    logger.info(f"  Has one_game template: {sports_template.one_item is not None}")
    logger.info(f"  Has two_games template: {sports_template.two_items is not None}")
    
    # Get stocks template
    stocks_template = loader.get_template('stocks')
    logger.info(f"✓ Loaded stocks template: {stocks_template.mode}")
    logger.info(f"  Canvas: {stocks_template.canvas_width}×{stocks_template.canvas_height}")
    
    return True


def test_custom_template_loading():
    """Test loading custom templates from config dict."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 2: Custom Template Loading")
    logger.info("=" * 60)
    
    from core.layout import LayoutLoader
    
    # Custom config with 64x64 panel
    config = {
        'display': {
            'ipixel': {
                'size_width': 64,
                'size_height': 64,
                'ble_addresses': ['TEST-ADDR']
            }
        },
        'layout_templates': {
            'sports': {
                'logo_enabled': True,
                'one_game': {
                    'away_logo': {'x': 4, 'y': 4, 'width': 24, 'height': 24},
                    'away_score': {'x': 32, 'y': 8, 'font_size': 16, 'color': 'away_team'},
                    'home_logo': {'x': 4, 'y': 36, 'width': 24, 'height': 24},
                    'home_score': {'x': 32, 'y': 40, 'font_size': 16, 'color': 'home_team'},
                }
            }
        }
    }
    
    loader = LayoutLoader(config)
    sports_template = loader.get_template('sports')
    
    logger.info(f"✓ Loaded custom template for 64×64 panel")
    logger.info(f"  Canvas: {sports_template.canvas_width}×{sports_template.canvas_height}")
    logger.info(f"  One game template:")
    logger.info(f"    Away logo: {sports_template.one_item.away_logo.x}, {sports_template.one_item.away_logo.y}")
    logger.info(f"    Away logo size: {sports_template.one_item.away_logo.width}×{sports_template.one_item.away_logo.height}")
    logger.info(f"    Away score font: {sports_template.one_item.away_score.font_size}px")
    
    return True


def test_sports_rendering():
    """Test sports rendering with templates."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 3: Sports Rendering")
    logger.info("=" * 60)
    
    from core.layout import LayoutLoader
    from core.rendering.templated_renderer import TemplatedSportsRenderer
    
    # Load default template
    loader = LayoutLoader({})
    template = loader.get_template('sports')
    renderer = TemplatedSportsRenderer(template)
    
    # Test data
    games = [
        {
            'home': 'DET',
            'away': 'BOS',
            'home_score': 5,
            'away_score': 3,
            'period': 'Q3',
            'clock': '8:42',
            'league': 'NBA',
            'state': 'inProgress'
        }
    ]
    
    # Render
    img = renderer.render_games(games, display_type='live')
    
    logger.info(f"✓ Rendered 1 game")
    logger.info(f"  Image size: {img.size}")
    logger.info(f"  Mode: {img.mode}")
    
    # Save test image
    img.save('/tmp/test_sports_1game.png')
    logger.info(f"  Saved: /tmp/test_sports_1game.png")
    
    # Test 2 games
    games_2 = games + [
        {
            'home': 'CHI',
            'away': 'MIA',
            'home_score': 102,
            'away_score': 98,
            'period': 'Q4',
            'clock': '2:15',
            'league': 'NBA',
            'state': 'inProgress'
        }
    ]
    
    img = renderer.render_games(games_2, display_type='live')
    img.save('/tmp/test_sports_2games.png')
    logger.info(f"✓ Rendered 2 games")
    logger.info(f"  Saved: /tmp/test_sports_2games.png")
    
    return True


def test_stocks_rendering():
    """Test stocks rendering with templates."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 4: Stocks Rendering")
    logger.info("=" * 60)
    
    from core.layout import LayoutLoader
    from core.rendering.templated_renderer import TemplatedStocksRenderer
    
    # Load default template
    loader = LayoutLoader({})
    template = loader.get_template('stocks')
    renderer = TemplatedStocksRenderer(template)
    
    # Test data
    quotes = [
        {
            'symbol': 'AAPL',
            'price': 185.50,
            'change': 2.50,
            'change_percent': 1.37,
            'is_up': True,
            'name': 'Apple Inc.'
        }
    ]
    
    # Render
    img = renderer.render_stocks(quotes)
    
    logger.info(f"✓ Rendered 1 stock")
    logger.info(f"  Image size: {img.size}")
    
    # Save test image
    img.save('/tmp/test_stocks_1stock.png')
    logger.info(f"  Saved: /tmp/test_stocks_1stock.png")
    
    # Test 4 stocks
    quotes_4 = quotes + [
        {'symbol': 'GOOGL', 'price': 142.15, 'change': -1.25, 'change_percent': -0.87, 'is_up': False},
        {'symbol': 'MSFT', 'price': 378.91, 'change': 3.22, 'change_percent': 0.86, 'is_up': True},
        {'symbol': 'TSLA', 'price': 238.72, 'change': 9.50, 'change_percent': 4.15, 'is_up': True},
    ]
    
    img = renderer.render_stocks(quotes_4)
    img.save('/tmp/test_stocks_4stocks.png')
    logger.info(f"✓ Rendered 4 stocks")
    logger.info(f"  Saved: /tmp/test_stocks_4stocks.png")
    
    return True


def test_large_panel_config():
    """Test rendering for 64×64 panel."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 5: Large Panel (64×64) Configuration")
    logger.info("=" * 60)
    
    from core.layout import LayoutLoader
    from core.rendering.templated_renderer import TemplatedSportsRenderer
    
    # Config for 64×64 panel with custom template
    config = {
        'display': {
            'ipixel': {
                'size_width': 64,
                'size_height': 64,
                'ble_addresses': ['TEST']
            }
        },
        'layout_templates': {
            'sports': {
                'logo_enabled': True,
                'one_game': {
                    'away_logo': {'x': 4, 'y': 4, 'width': 24, 'height': 24},
                    'away_score': {'x': 32, 'y': 12, 'font_size': 18, 'color': 'away_team'},
                    'home_logo': {'x': 4, 'y': 36, 'width': 24, 'height': 24},
                    'home_score': {'x': 32, 'y': 44, 'font_size': 18, 'color': 'home_team'},
                    'period': {'x': 4, 'y': 4, 'font_size': 10, 'align': 'right', 'color': 'time'},
                    'clock': {'x': 4, 'y': 16, 'font_size': 10, 'align': 'right', 'color': 'time'},
                }
            }
        }
    }
    
    loader = LayoutLoader(config)
    template = loader.get_template('sports')
    renderer = TemplatedSportsRenderer(template)
    
    logger.info(f"✓ Created renderer for 64×64 panel")
    logger.info(f"  Canvas: {template.canvas_width}×{template.canvas_height}")
    
    # Render test game
    games = [{
        'home': 'DET', 'away': 'BOS',
        'home_score': 5, 'away_score': 3,
        'period': 'Q3', 'clock': '8:42',
        'league': 'NBA', 'state': 'inProgress'
    }]
    
    img = renderer.render_games(games)
    img.save('/tmp/test_sports_64x64.png')
    logger.info(f"  Rendered and saved: /tmp/test_sports_64x64.png")
    logger.info(f"  Larger logos (24×24) and fonts (18px) for big panel")
    
    return True


def run_all_tests():
    """Run all tests."""
    logger.info("\n" + "=" * 60)
    logger.info("LAYOUT TEMPLATES SYSTEM TEST SUITE")
    logger.info("=" * 60 + "\n")
    
    tests = [
        ("Layout Loader", test_layout_loader),
        ("Custom Template Loading", test_custom_template_loading),
        ("Sports Rendering", test_sports_rendering),
        ("Stocks Rendering", test_stocks_rendering),
        ("Large Panel Config", test_large_panel_config),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                logger.error(f"✗ {name} FAILED")
        except Exception as e:
            failed += 1
            logger.error(f"✗ {name} FAILED with exception:")
            logger.error(f"  {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    logger.info(f"✓ Passed: {passed}/{len(tests)}")
    if failed > 0:
        logger.error(f"✗ Failed: {failed}/{len(tests)}")
    else:
        logger.info("🎉 ALL TESTS PASSED!")
    logger.info("")
    logger.info("Test images saved to /tmp/")
    logger.info("  - test_sports_1game.png")
    logger.info("  - test_sports_2games.png")
    logger.info("  - test_sports_64x64.png")
    logger.info("  - test_stocks_1stock.png")
    logger.info("  - test_stocks_4stocks.png")
    logger.info("")
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)

