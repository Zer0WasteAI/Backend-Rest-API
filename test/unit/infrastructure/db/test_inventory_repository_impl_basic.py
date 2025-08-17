from types import SimpleNamespace
from unittest.mock import MagicMock
from datetime import datetime, timezone, timedelta


class FakeExecuteResult:
    def __init__(self, items=None, scalar=None, scalar_count=None):
        self._items = items or []
        self._scalar = scalar
        self._scalar_count = scalar_count

    def scalars(self):
        return SimpleNamespace(all=lambda: self._items)

    def scalar_one_or_none(self):
        return self._scalar

    def scalar(self):
        return self._scalar_count


class FakeSession:
    def __init__(self):
        self.add = MagicMock()
        self.commit = MagicMock()
        self.flush = MagicMock()
        self.get = MagicMock(return_value=None)
        self._execute_result = FakeExecuteResult()

    def execute(self, stmt):
        return self._execute_result


class FakeDB:
    def __init__(self, session):
        self.session = session


def make_fake_ingredient(name='Tomato'):
    stack1 = SimpleNamespace(quantity=10, expiration_date=datetime.now(timezone.utc)+timedelta(days=1), added_at=datetime.now(timezone.utc))
    fake = SimpleNamespace(
        name=name,
        type_unit='g',
        storage_type='fridge',
        tips='',
        image_path='',
        stacks=[stack1]
    )
    return fake


def test_get_by_user_uid_maps_to_domain():
    session = FakeSession()
    session._execute_result = FakeExecuteResult(items=[make_fake_ingredient()])
    db = FakeDB(session)
    from src.infrastructure.db.inventory_repository_impl import InventoryRepositoryImpl
    repo = InventoryRepositoryImpl(db)
    inv = repo.get_by_user_uid('u1')
    assert inv is not None
    assert 'Tomato' in inv.ingredients


def test_delete_ingredient_complete_commits():
    session = FakeSession()
    session._execute_result = FakeExecuteResult()  # rowcount not used by MagicMock execute default
    db = FakeDB(session)
    from src.infrastructure.db.inventory_repository_impl import InventoryRepositoryImpl
    repo = InventoryRepositoryImpl(db)
    repo.delete_ingredient_complete('u1', 'Tomato')
    session.commit.assert_called_once()

