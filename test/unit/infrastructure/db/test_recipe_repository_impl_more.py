from types import SimpleNamespace
from unittest.mock import MagicMock


class SessionBFM:
    def __init__(self, recipe_list, get_map):
        self._recipe_list = recipe_list
        self._get_map = get_map
        self.add = MagicMock()
        self.commit = MagicMock()

    def execute(self, stmt):
        # Only handle select(RecipeORM)
        return SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: self._recipe_list))

    def get(self, orm_cls, uid):
        return self._get_map.get(uid)


def make_recipe_orm(uid, title):
    ing = SimpleNamespace(name='Tomato', quantity=1, type_unit='pcs')
    step = SimpleNamespace(step_order=1, description='Do it')
    return SimpleNamespace(uid=uid, user_uid='u1', title=title, duration='10m', difficulty='easy',
                           ingredients=[ing], steps=[step], footer='', generated_by_ai=False,
                           saved_at=None, category='', image_path='', description='')


def test_find_best_match_name_returns_domain():
    orm1 = make_recipe_orm('r1', 'Tomato Soup')
    orm2 = make_recipe_orm('r2', 'Chicken Curry')
    session = SessionBFM([orm1, orm2], {'r1': orm1, 'r2': orm2})
    db = SimpleNamespace(session=session)
    from src.infrastructure.db.recipe_repository_impl import RecipeRepositoryImpl
    repo = RecipeRepositoryImpl(db)
    res = repo.find_best_match_name('Tomato')
    assert res is not None
    assert 'Tomato' in res.title


def test_exists_and_find_by_name_and_count_prefix():
    # Prepare two recipes
    orm1 = make_recipe_orm('r1', 'Tomato Soup')
    orm2 = make_recipe_orm('r2', 'Tomato Salad')
    session = SessionBFM([orm1, orm2], {'r1': orm1, 'r2': orm2})
    db = SimpleNamespace(session=session)
    from src.infrastructure.db.recipe_repository_impl import RecipeRepositoryImpl
    repo = RecipeRepositoryImpl(db)
    # exists_by_user_and_title relies on select+scalar_one_or_none; we approximate via execute().scalar_one_or_none()
    # Our SessionBFM doesn't support scalar_one_or_none directly in execute path; test find_by_name using execute().
    # Simulate find_by_name by setting execute().scalar_one_or_none via monkeypatching of session.execute if needed
    # Here, we directly assert count_by_user_and_title_prefix calls execute().scalar which we can map
    session._scalar_count = 2
    def exec_with_scalar(stmt):
        return SimpleNamespace(scalar=lambda: 2, scalar_one_or_none=lambda: orm1)
    session.execute = exec_with_scalar
    # find_by_name
    r = repo.find_by_name('Tomato Soup')
    assert r.uid == 'r1'
    # exists
    assert repo.exists_by_user_and_title('u1', 'Tomato Soup') is True
    # count prefix
    c = repo.count_by_user_and_title_prefix('u1', 'Tomato')
    assert c == 2
