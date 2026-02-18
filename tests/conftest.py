"""
Pytest configuration and shared fixtures for testing.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta


@pytest.fixture
def mock_httpx_response():
    """Create a mock httpx response."""
    def _create_response(json_data=None, status_code=200):
        mock_response = MagicMock()
        mock_response.status_code = status_code
        mock_response.json.return_value = json_data or {}
        mock_response.raise_for_status = MagicMock()
        if status_code >= 400:
            from httpx import HTTPStatusError
            mock_response.raise_for_status.side_effect = HTTPStatusError(
                f"HTTP {status_code}",
                request=MagicMock(),
                response=mock_response
            )
        return mock_response
    return _create_response


@pytest.fixture
def mock_httpx_client(mock_httpx_response):
    """Create a mock httpx AsyncClient."""
    async def _create_client(response_data=None, status_code=200):
        mock_client = AsyncMock()
        mock_client.is_closed = False
        mock_client.request = AsyncMock(
            return_value=mock_httpx_response(response_data, status_code)
        )
        mock_client.aclose = AsyncMock()
        return mock_client
    return _create_client


@pytest.fixture
def sample_weather_data():
    """Sample weather API response."""
    return {
        'name': 'Test City',
        'main': {
            'temp': 72.5,
            'feels_like': 70.0,
            'temp_min': 68.0,
            'temp_max': 75.0,
            'humidity': 65
        },
        'weather': [
            {'main': 'Clear', 'description': 'clear sky'}
        ],
        'wind': {
            'speed': 10.5
        }
    }


@pytest.fixture
def sample_forecast_data():
    """Sample forecast API response."""
    return {
        'list': [
            {
                'dt': int((datetime.now() + timedelta(hours=i)).timestamp()),
                'main': {
                    'temp': 70 + i,
                    'feels_like': 68 + i,
                    'temp_min': 65 + i,
                    'temp_max': 72 + i,
                    'humidity': 60
                },
                'weather': [
                    {'main': 'Clear', 'description': 'clear sky'}
                ],
                'wind': {'speed': 8.0},
                'dt_txt': (datetime.now() + timedelta(hours=i)).strftime('%Y-%m-%d %H:%M:%S')
            }
            for i in range(40)  # 5 days of 3-hour forecasts
        ]
    }


@pytest.fixture
def sample_sports_data():
    """Sample ESPN sports API response."""
    return {
        'events': [
            {
                'id': '401234567',
                'name': 'Boston Celtics at Los Angeles Lakers',
                'shortName': 'BOS @ LAL',
                'date': datetime.now().isoformat(),
                'competitions': [{
                    'competitors': [
                        {
                            'team': {
                                'abbreviation': 'BOS',
                                'displayName': 'Boston Celtics',
                                'logo': 'https://example.com/bos.png'
                            },
                            'score': '95',
                            'homeAway': 'away'
                        },
                        {
                            'team': {
                                'abbreviation': 'LAL',
                                'displayName': 'Los Angeles Lakers',
                                'logo': 'https://example.com/lal.png'
                            },
                            'score': '102',
                            'homeAway': 'home'
                        }
                    ],
                    'status': {
                        'type': {
                            'name': 'STATUS_FINAL',
                            'completed': True
                        },
                        'displayClock': '0:00',
                        'period': 4
                    }
                }]
            }
        ]
    }


@pytest.fixture
def sample_stocks_data():
    """Sample yfinance stocks data."""
    return [
        {
            'symbol': 'AAPL',
            'price': 195.50,
            'change': 4.25,
            'change_percent': 2.22,
            'is_up': True
        },
        {
            'symbol': 'GOOGL',
            'price': 142.75,
            'change': -1.30,
            'change_percent': -0.90,
            'is_up': False
        }
    ]


@pytest.fixture
def sample_screener_data():
    """Sample yfinance screener data."""
    return {
        'quotes': [
            {
                'symbol': 'TSLA',
                'regularMarketPrice': 245.10,
                'regularMarketChange': 15.75,
                'regularMarketChangePercent': 6.87
            },
            {
                'symbol': 'NVDA',
                'regularMarketPrice': 875.30,
                'regularMarketChange': 42.50,
                'regularMarketChangePercent': 5.10
            }
        ]
    }


@pytest.fixture(autouse=True)
def reset_time():
    """Reset time-based caches between tests."""
    yield
    # Cleanup after each test
    import gc
    gc.collect()


