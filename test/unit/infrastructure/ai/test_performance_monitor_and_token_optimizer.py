import pytest
from src.infrastructure.ai.performance_monitor import performance_monitor, OperationTracker


def test_operation_tracker_records_metrics():
    performance_monitor.reset_metrics()
    with OperationTracker('recipe_generation', metadata={'hint': 'test'}) as t:
        t.set_cache_hit(True)
        t.set_tokens_used(123)
        # Simulate work
        _ = 1 + 1
    stats = performance_monitor.get_stats('recipe_generation')
    assert 'recipe_generation' in stats
    st = stats['recipe_generation']
    assert st.total_requests >= 1
    summary = performance_monitor.get_performance_summary()
    assert summary['summary']['total_requests'] >= 1
    exported = performance_monitor.export_metrics('recipe_generation', hours_back=1)
    assert len(exported) >= 1

