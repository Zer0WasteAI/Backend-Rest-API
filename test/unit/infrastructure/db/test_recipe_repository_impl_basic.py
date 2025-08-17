from types import SimpleNamespace
from unittest.mock import MagicMock


class FakeSession:
    def __init__(self):
        self.add = MagicMock()
        self.commit = MagicMock()
        self.get = MagicMock()
        self._execute_result = SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: []))

    def execute(self, stmt):
        return self._execute_result


class FakeDB:
    def __init__(self, session):
        self.session = session


def test_find_by_uid_maps_domain():
    session = FakeSession()
    # Fake ORM recipe with relations
    ing = SimpleNamespace(name='Tomato', quantity=1, type_unit='pcs')
    step = SimpleNamespace(step_order=1, description='Do it')
    orm = SimpleNamespace(uid='r1', user_uid='u1', title='T', duration='10m', difficulty='easy',
                          ingredients=[ing], steps=[step], footer='', generated_by_ai=False,
                          saved_at=None, category='', image_path='', description='')
    session.get.return_value = orm
    db = FakeDB(session)
    from src.infrastructure.db.recipe_repository_impl import RecipeRepositoryImpl
    repo = RecipeRepositoryImpl(db)
    r = repo.find_by_uid('r1')
    assert r.uid == 'r1'
    assert len(r.ingredients) == 1
    assert len(r.steps) == 1


def test_save_adds_and_commits():
    session = FakeSession()
    db = FakeDB(session)
    from src.infrastructure.db.recipe_repository_impl import RecipeRepositoryImpl
    from src.domain.models.recipe import Recipe, RecipeIngredient, RecipeStep
    repo = RecipeRepositoryImpl(db)
    recipe = Recipe(uid='r1', user_uid='u1', title='T', duration='10m', difficulty='easy',
                    ingredients=[RecipeIngredient('Tomato', 1, 'pcs')],
                    steps=[RecipeStep(1, 'Do it')], footer='', generated_by_ai=False,
                    saved_at=None, category='', image_path='', description='')
    repo.save(recipe)
    assert session.add.call_count >= 3  # recipe + ingredient + step
    session.commit.assert_called_once()

