from src.config.optimization_config import OptimizationConfig


def test_cache_config_contains_expected_keys():
    cfg = OptimizationConfig.get_cache_config()
    assert cfg["CACHE_TYPE"] == OptimizationConfig.CACHE_TYPE
    assert "CACHE_REDIS_URL" in cfg
    assert "CACHE_DEFAULT_TIMEOUT" in cfg
    assert "CACHE_REDIS_CONNECTION_POOL_KWARGS" in cfg


def test_limiter_config_contains_expected_keys():
    cfg = OptimizationConfig.get_limiter_config()
    assert cfg["RATELIMIT_STORAGE_URL"].startswith("redis://")
    assert cfg["RATELIMIT_DEFAULT"]


def test_getters_return_values():
    assert OptimizationConfig.get_rate_limit("auth_login")
    assert isinstance(OptimizationConfig.get_cache_timeout("inventory_basic"), int)
    key = OptimizationConfig.get_cache_key("user_inventory", user_id="u1")
    assert key.startswith("inventory:user:u1")

