from types import SimpleNamespace
from unittest.mock import MagicMock
from datetime import datetime, timezone


class QueueExecuteResult:
    def __init__(self, scalar_queue=None, scalars_list=None):
        self.scalar_queue = scalar_queue or []
        self.scalars_list = scalars_list or []

    def scalars(self):
        return SimpleNamespace(all=lambda: self.scalars_list)

    def scalar_one_or_none(self):
        if self.scalar_queue:
            return self.scalar_queue.pop(0)
        return None


class SessionWithQueue:
    def __init__(self):
        self.add = MagicMock()
        self.commit = MagicMock()
        self.flush = MagicMock()
        self.get = MagicMock(return_value=None)
        self._result = QueueExecuteResult()

    def set_scalar_queue(self, items):
        self._result.scalar_queue = list(items)

    def set_scalars_list(self, items):
        self._result.scalars_list = items

    def execute(self, stmt):
        return self._result


class FakeDB:
    def __init__(self, session):
        self.session = session


def test_add_ingredient_stack_creates_new_when_missing():
    session = SessionWithQueue()
    # First select for existing ingredient returns None
    session.set_scalar_queue([None])
    db = FakeDB(session)
    from src.infrastructure.db.inventory_repository_impl import InventoryRepositoryImpl
    from src.domain.models.ingredient import Ingredient, IngredientStack
    repo = InventoryRepositoryImpl(db)
    ing = Ingredient('Tomato', 'g', 'fridge', tips='', image_path='')
    stack = IngredientStack(1, 'g', datetime.now(timezone.utc), datetime.now(timezone.utc))
    repo.add_ingredient_stack('u1', stack, ing)
    # Created ingredient + stack and committed
    assert session.flush.called
    assert session.commit.called


def test_add_ingredient_stack_updates_when_exists():
    session = SessionWithQueue()
    existing = SimpleNamespace(name='Tomato', type_unit='x', storage_type='x', tips='x', image_path='x')
    session.set_scalar_queue([existing])
    db = FakeDB(session)
    from src.infrastructure.db.inventory_repository_impl import InventoryRepositoryImpl
    from src.domain.models.ingredient import Ingredient, IngredientStack
    repo = InventoryRepositoryImpl(db)
    ing = Ingredient('Tomato', 'g', 'fridge', tips='', image_path='')
    stack = IngredientStack(1, 'g', datetime.now(timezone.utc), datetime.now(timezone.utc))
    repo.add_ingredient_stack('u1', stack, ing)
    # Existing updated, stack added, committed
    assert existing.type_unit == 'g'
    assert session.commit.called


def test_get_food_item_returns_dict():
    session = SessionWithQueue()
    food = SimpleNamespace(
        name='Pizza', main_ingredients=[], category='prepared', calories=800, description='',
        storage_type='fridge', expiration_time=2, time_unit='days', tips='', serving_quantity=2,
        image_path='', added_at=datetime.now(timezone.utc), expiration_date=datetime.now(timezone.utc)
    )
    session.set_scalar_queue([food])
    db = FakeDB(session)
    from src.infrastructure.db.inventory_repository_impl import InventoryRepositoryImpl
    repo = InventoryRepositoryImpl(db)
    res = repo.get_food_item('u1', 'Pizza', '2024-01-01T00:00:00Z')
    assert res['name'] == 'Pizza'


def test_get_all_food_items_returns_list():
    session = SessionWithQueue()
    food1 = SimpleNamespace(
        name='Pizza', main_ingredients=[], category='prepared', calories=800, description='',
        storage_type='fridge', expiration_time=2, time_unit='days', tips='', serving_quantity=2,
        image_path='', added_at=datetime.now(timezone.utc), expiration_date=datetime.now(timezone.utc)
    )
    food2 = SimpleNamespace(
        name='Soup', main_ingredients=[], category='soup', calories=200, description='',
        storage_type='fridge', expiration_time=1, time_unit='days', tips='', serving_quantity=1,
        image_path='', added_at=datetime.now(timezone.utc), expiration_date=datetime.now(timezone.utc)
    )
    session.set_scalars_list([food1, food2])
    db = FakeDB(session)
    from src.infrastructure.db.inventory_repository_impl import InventoryRepositoryImpl
    repo = InventoryRepositoryImpl(db)
    res = repo.get_all_food_items('u1')
    assert isinstance(res, list) and len(res) == 2
    assert res[0]['name'] in ['Pizza', 'Soup']


def test_get_all_ingredient_stacks_returns_list():
    session = SessionWithQueue()
    stack1 = SimpleNamespace(quantity=1, added_at=datetime.now(timezone.utc), expiration_date=datetime.now(timezone.utc))
    stack2 = SimpleNamespace(quantity=2, added_at=datetime.now(timezone.utc), expiration_date=datetime.now(timezone.utc))
    session.set_scalars_list([stack1, stack2])
    db = FakeDB(session)
    from src.infrastructure.db.inventory_repository_impl import InventoryRepositoryImpl
    repo = InventoryRepositoryImpl(db)
    stacks = repo.get_all_ingredient_stacks('u1', 'Tomato')
    assert isinstance(stacks, list) and len(stacks) == 2


def test_delete_ingredient_stack_commits():
    session = SessionWithQueue()
    db = FakeDB(session)
    from src.infrastructure.db.inventory_repository_impl import InventoryRepositoryImpl
    repo = InventoryRepositoryImpl(db)
    repo.delete_ingredient_stack('u1', 'Tomato', '2024-01-01T00:00:00Z')
    assert session.commit.called
