import types
from flask import Flask

from src.infrastructure.optimization.cache_service import cache_service


def make_app(testing: bool = False) -> Flask:
    app = Flask(__name__)
    app.config.update({
        "TESTING": testing,
    })
    return app


def test_cache_service_disabled_in_testing():
    app = make_app(testing=True)
    cache_service.init_app(app)
    # In testing mode, cache is disabled by design
    assert cache_service.enabled is False
    assert cache_service.cache is None


def test_cache_service_fallback_to_simple_when_redis_unavailable():
    app = make_app(testing=False)
    # Try init; if Redis is not reachable, service should fallback to simple cache
    cache_service.init_app(app)
    assert cache_service.enabled is True
    assert cache_service.cache is not None
    # Set/Get should work
    ok = cache_service.set("unit:key", {"v": 1}, timeout=5)
    assert ok is True
    val = cache_service.get("unit:key")
    assert isinstance(val, dict) and val.get("v") == 1

