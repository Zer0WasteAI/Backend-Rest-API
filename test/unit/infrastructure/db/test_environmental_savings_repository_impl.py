from types import SimpleNamespace
from unittest.mock import MagicMock


class FakeResult:
    def __init__(self, fetchone=None, fetchall=None):
        self._one = fetchone
        self._all = fetchall or []
    def fetchone(self):
        return self._one
    def fetchall(self):
        return self._all


class FakeSession:
    def __init__(self):
        self.execute = MagicMock(return_value=FakeResult())
        self.commit = MagicMock()
        self.rollback = MagicMock()


class FakeDB:
    def __init__(self, session):
        self.session = session


def make_savings_row():
    return SimpleNamespace(
        user_uid='u1', recipe_uid='r1', recipe_title='T', recipe_source_type='manual',
        carbon_footprint=1.0, water_footprint=2.0, energy_footprint=3.0, economic_cost=4.0,
        unit_carbon='kg', unit_water='l', unit_energy='kWh', unit_cost='S/', is_cooked=False, saved_at=None, id='s1'
    )


def test_save_insert_and_update_paths():
    from src.infrastructure.db.environmental_savings_repository_impl import EnvironmentalSavingsRepositoryImpl
    from src.domain.models.environmental_savings import EnvironmentalSavings
    session = FakeSession()
    # First call: find_by_user_and_recipe -> None; then insert; Second call: find_by_user_and_recipe -> row; then update
    row = make_savings_row()
    session.execute.side_effect = [
        FakeResult(fetchone=None),  # save: find_by_user_and_recipe => insert
        FakeResult(),               # execute insert
        FakeResult(fetchone=(row,)),# save: find_by_user_and_recipe => update
        FakeResult(),               # execute update
    ]
    repo = EnvironmentalSavingsRepositoryImpl(FakeDB(session))
    savings = EnvironmentalSavings(
        user_uid=row.user_uid, recipe_uid=row.recipe_uid, recipe_title=row.recipe_title,
        carbon_footprint=row.carbon_footprint, water_footprint=row.water_footprint,
        energy_footprint=row.energy_footprint, economic_cost=row.economic_cost,
        unit_carbon=row.unit_carbon, unit_water=row.unit_water, unit_energy=row.unit_energy,
        unit_cost=row.unit_cost, is_cooked=row.is_cooked
    )
    repo.save(savings)
    repo.save(savings)
    assert session.commit.call_count >= 2


def test_find_by_user_and_uid_and_status_and_update_type_status():
    from src.infrastructure.db.environmental_savings_repository_impl import EnvironmentalSavingsRepositoryImpl
    session = FakeSession()
    row = make_savings_row()
    session.execute.side_effect = [
        FakeResult(fetchall=[(row,)]),  # find_by_user
        FakeResult(fetchone=(row,)),    # find_by_uid
        FakeResult(fetchall=[(row,)]),  # find_by_user_and_by_is_cooked
        FakeResult(),                   # update_type_status
    ]
    repo = EnvironmentalSavingsRepositoryImpl(FakeDB(session))
    all_ = repo.find_by_user('u1')
    assert len(all_) == 1 and all_[0].recipe_uid == 'r1'
    one = repo.find_by_uid('s1')
    assert one.recipe_uid == 'r1'
    cooked = repo.find_by_user_and_by_is_cooked('u1', False)
    assert len(cooked) == 1
    repo.update_type_status('s1', True)
    session.commit.assert_called()


def test_find_by_user_and_recipe_and_delete_and_update_validation_status():
    from src.infrastructure.db.environmental_savings_repository_impl import EnvironmentalSavingsRepositoryImpl
    session = FakeSession()
    row = make_savings_row()
    session.execute.side_effect = [
        FakeResult(fetchone=(row,)),  # find_by_user_and_recipe
        FakeResult(),                 # delete
        FakeResult(),                 # update_validation_status -> delegates to update_type_status
    ]
    repo = EnvironmentalSavingsRepositoryImpl(FakeDB(session))
    r = repo.find_by_user_and_recipe('u1', 'r1')
    assert r.recipe_uid == 'r1'
    repo.delete('s1')
    repo.update_validation_status('s1', True)
    session.commit.assert_called()

