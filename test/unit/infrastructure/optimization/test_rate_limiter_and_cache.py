import pytest
from unittest.mock import MagicMock, patch

from src.infrastructure.optimization.rate_limiter import rate_limiter, smart_rate_limit, get_rate_limit_status
from src.infrastructure.optimization.cache_service import cache_service, smart_cache, cache_user_data


def test_smart_rate_limit_no_limiter_executes_function():
    # Ensure limiter is disabled
    rate_limiter.limiter = None

    @smart_rate_limit('any')
    def f():
        return 'ok'

    assert f() == 'ok'


def test_get_rate_limit_status_when_disabled():
    rate_limiter.limiter = None
    status = get_rate_limit_status()
    assert status['status'] == 'disabled'


def test_smart_cache_decorator_uses_cache_when_enabled():
    cache_service.enabled = True
    cache_service.get = MagicMock(return_value=None)
    cache_service.set = MagicMock()

    calls = {'count': 0}

    @smart_cache('test', timeout=10)
    def compute(x):
        calls['count'] += 1
        return x * 2

    # First call populates cache
    assert compute(3) == 6
    assert calls['count'] == 1
    cache_service.set.assert_called_once()


@patch('src.infrastructure.optimization.cache_service.get_jwt_identity')
def test_cache_user_data_adds_user_scope(mock_identity):
    cache_service.enabled = True
    cache_service.get = MagicMock(return_value=None)
    cache_service.set = MagicMock()
    mock_identity.return_value = 'user-1'

    calls = {'count': 0}

    @cache_user_data('foo', timeout=5)
    def expensive(a):
        calls['count'] += 1
        return a + 1

    assert expensive(10) == 11
    assert calls['count'] == 1
    cache_service.set.assert_called_once()

