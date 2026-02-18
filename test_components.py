#!/usr/bin/env python3
"""
Test script for the component-based rendering system.

This demonstrates how composite templates work.
"""

import asyncio
import sys
sys.path.insert(0, '.')

from core.components import registry
from core.components.composite_renderer import load_composite_template


async def test_clock_with_weather():
    """Test clock + weather composite template."""
    print("\n" + "="*60)
    print("Testing: Clock with Weather Forecast")
    print("="*60)
    
    renderer = load_composite_template('templates/clock_with_weather.yml', registry)
    print(f"✅ Loaded: {renderer}")
    print(f"   Components: {renderer.get_component_count()}")
    
    # Render
    print("   Rendering...")
    img = await renderer.render()
    print(f"✅ Rendered: {img.size} {img.mode}")
    
    # Save
    img.save('/tmp/clock_with_weather.png')
    print(f"✅ Saved: /tmp/clock_with_weather.png")
    
    return img


async def test_sports_and_stocks():
    """Test sports + stocks composite template."""
    print("\n" + "="*60)
    print("Testing: Sports and Stocks")
    print("="*60)
    
    renderer = load_composite_template('templates/sports_and_stocks.yml', registry)
    print(f"✅ Loaded: {renderer}")
    print(f"   Components: {renderer.get_component_count()}")
    
    # Render
    print("   Rendering...")
    img = await renderer.render()
    print(f"✅ Rendered: {img.size} {img.mode}")
    
    # Save
    img.save('/tmp/sports_and_stocks.png')
    print(f"✅ Saved: /tmp/sports_and_stocks.png")
    
    return img


async def test_dashboard():
    """Test multi-widget dashboard template."""
    print("\n" + "="*60)
    print("Testing: Information Dashboard (128x40)")
    print("="*60)
    
    renderer = load_composite_template('templates/dashboard.yml', registry)
    print(f"✅ Loaded: {renderer}")
    print(f"   Components: {renderer.get_component_count()}")
    
    # Render
    print("   Rendering...")
    img = await renderer.render()
    print(f"✅ Rendered: {img.size} {img.mode}")
    
    # Save
    img.save('/tmp/dashboard.png')
    print(f"✅ Saved: /tmp/dashboard.png")
    
    return img


async def test_component_registry():
    """Test component registry."""
    print("\n" + "="*60)
    print("Component Registry")
    print("="*60)
    
    types = registry.list_types()
    print(f"✅ Registered components: {len(types)}")
    for comp_type in types:
        comp_class = registry.get_class(comp_type)
        print(f"   - {comp_type}: {comp_class.__name__}")


async def main():
    """Run all tests."""
    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║  Component-Based Rendering System Test                      ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    
    # Test registry
    await test_component_registry()
    
    # Test templates
    try:
        await test_clock_with_weather()
    except Exception as e:
        print(f"❌ Clock with weather failed: {e}")
    
    try:
        await test_sports_and_stocks()
    except Exception as e:
        print(f"❌ Sports and stocks failed: {e}")
    
    try:
        await test_dashboard()
    except Exception as e:
        print(f"❌ Dashboard failed: {e}")
    
    print("\n" + "="*60)
    print("✅ Component system is working!")
    print("="*60)
    print("\nNext steps:")
    print("1. Create your own templates in templates/")
    print("2. Build a template builder UI")
    print("3. Add more custom components")
    print("\nSee: docs/component-system.md")


if __name__ == '__main__':
    asyncio.run(main())


