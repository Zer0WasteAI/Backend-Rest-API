from types import SimpleNamespace
from unittest.mock import MagicMock
from datetime import date, datetime


def test_find_by_user_returns_domain_list():
    from src.infrastructure.db.waste_log_repository_impl import WasteLogRepository
    session = MagicMock()
    # Build query chain to return .all()
    waste_orm = SimpleNamespace(
        waste_id='w1', batch_id='b1', user_uid='u1', reason='EXPIRED', estimated_weight=100.0,
        unit='g', waste_date=date.today(), ingredient_uid='ing_tomato', co2e_wasted_kg=0.1,
        created_at=datetime.now(), updated_at=datetime.now()
    )
    query_mock = MagicMock()
    query_mock.all.return_value = [waste_orm]
    session.query.return_value.filter_by.return_value.order_by.return_value = query_mock
    repo = WasteLogRepository(SimpleNamespace(session=session))
    res = repo.find_by_user('u1')
    assert isinstance(res, list) and len(res) == 1
    assert res[0].waste_id == 'w1'

