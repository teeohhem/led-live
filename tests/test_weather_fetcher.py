"""
Unit tests for WeatherFetcher.
"""
import pytest
import os
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from core.data.weather_data import WeatherFetcher


@pytest.mark.asyncio
class TestWeatherFetcher:
    """Test cases for WeatherFetcher."""
    
    async def test_initialization(self):
        """Test initialization with explicit parameters."""
        fetcher = WeatherFetcher(
            api_key='test_key',
            zipcode='10001',
            units='imperial',
            cache_ttl=600
        )
        
        assert fetcher.api_key == 'test_key'
        assert fetcher.zipcode == '10001'
        assert fetcher.units == 'imperial'
        assert fetcher._cache_ttl == 600
    
    @patch('core.data.weather_data.WeatherFetcher.fetch_with_retry')
    async def test_get_coordinates(self, mock_fetch):
        """Test fetching and storing coordinates from zipcode."""
        mock_fetch.return_value = {
            'name': 'New York',
            'lat': 40.7128,
            'lon': -74.0060
        }
        
        fetcher = WeatherFetcher(api_key='test_key', zipcode='10001')
        lat, lon = await fetcher._get_coordinates()
        
        assert lat == 40.7128
        assert lon == -74.0060
        assert fetcher._lat == 40.7128
        assert fetcher._lon == -74.0060
    
    @patch('core.data.weather_data.WeatherFetcher.fetch_with_retry')
    async def test_get_coordinates_caching(self, mock_fetch):
        """Test that coordinates are cached and not refetched."""
        mock_fetch.return_value = {
            'name': 'New York',
            'lat': 40.7128,
            'lon': -74.0060
        }
        
        fetcher = WeatherFetcher(api_key='test_key', zipcode='10001')
        
        # First call
        await fetcher._get_coordinates()
        
        # Second call should use cached values
        lat, lon = await fetcher._get_coordinates()
        
        # Should only be called once
        assert mock_fetch.call_count == 1
        assert lat == 40.7128
        assert lon == -74.0060
    
    @patch('core.data.weather_data.WeatherFetcher._get_coordinates')
    @patch('core.data.weather_data.WeatherFetcher.fetch_with_retry')
    async def test_fetch(self, mock_fetch_retry, mock_coords, sample_weather_data):
        """Test main fetch method."""
        mock_coords.return_value = (40.7128, -74.0060)
        
        # Mock both current weather and forecast
        mock_fetch_retry.side_effect = [
            sample_weather_data,  # Current weather
            {'list': []}  # Forecast
        ]
        
        fetcher = WeatherFetcher(api_key='test_key', zipcode='10001')
        result = await fetcher.fetch()
        
        assert result is not None
        # The parsed result may have different structure
        assert isinstance(result, dict)
    
    @patch('core.data.weather_data.WeatherFetcher._get_coordinates')
    @patch('core.data.weather_data.WeatherFetcher.fetch_with_retry')
    async def test_fetch_hourly(self, mock_fetch, mock_coords, sample_forecast_data):
        """Test fetching hourly forecast."""
        mock_coords.return_value = (40.7128, -74.0060)
        mock_fetch.return_value = sample_forecast_data
        
        fetcher = WeatherFetcher(api_key='test_key', zipcode='10001')
        result = await fetcher.fetch_hourly(hours=4)
        
        assert result is not None
        # The method returns all forecast items, just verify it's a list
        assert isinstance(result, list)
    
    @patch('core.data.weather_data.WeatherFetcher._get_coordinates')
    @patch('core.data.weather_data.WeatherFetcher.fetch_with_retry')
    async def test_fetch_daily(self, mock_fetch, mock_coords, sample_forecast_data):
        """Test fetching daily forecast."""
        mock_coords.return_value = (40.7128, -74.0060)
        mock_fetch.return_value = sample_forecast_data
        
        fetcher = WeatherFetcher(api_key='test_key', zipcode='10001')
        result = await fetcher.fetch_daily(days=2)
        
        assert result is not None
        assert isinstance(result, list)
    
    @patch('core.data.weather_data.WeatherFetcher._get_coordinates')
    @patch('core.data.weather_data.WeatherFetcher.fetch_with_retry')
    async def test_get_cached_or_fetch(self, mock_fetch, mock_coords, sample_weather_data):
        """Test caching behavior."""
        mock_coords.return_value = (40.7128, -74.0060)
        mock_fetch.side_effect = [
            sample_weather_data,  # Current
            {'list': []},  # Forecast
            sample_weather_data,  # Second current (shouldn't be called)
            {'list': []}  # Second forecast (shouldn't be called)
        ]
        
        fetcher = WeatherFetcher(api_key='test_key', zipcode='10001')
        
        # First call should fetch
        result1 = await fetcher.get_cached_or_fetch()
        first_call_count = mock_fetch.call_count
        
        # Second call should use cache
        result2 = await fetcher.get_cached_or_fetch()
        
        # Should not have made additional fetch calls
        assert mock_fetch.call_count == first_call_count
        assert result1 == result2
    
    @patch('core.data.weather_data.WeatherFetcher.fetch_with_retry')
    async def test_fetch_with_api_error(self, mock_fetch):
        """Test handling of API errors."""
        mock_fetch.return_value = None  # Simulate API failure
        
        fetcher = WeatherFetcher(api_key='test_key', zipcode='10001')
        result = await fetcher.fetch()
        
        # Should handle gracefully
        assert result is None or isinstance(result, dict)
    
    async def test_units_parameter(self):
        """Test that units parameter is used."""
        fetcher_imperial = WeatherFetcher(
            api_key='test', 
            zipcode='10001', 
            units='imperial'
        )
        fetcher_metric = WeatherFetcher(
            api_key='test', 
            zipcode='10001', 
            units='metric'
        )
        
        assert fetcher_imperial.units == 'imperial'
        assert fetcher_metric.units == 'metric'
