from types import SimpleNamespace
from unittest.mock import MagicMock
from datetime import date
import pytest


class FakeResult:
    def __init__(self, scalar_one_or_none=None, scalars_all=None):
        self._one = scalar_one_or_none
        self._all = scalars_all or []
    def scalar_one_or_none(self):
        return self._one
    def scalars(self):
        return SimpleNamespace(all=lambda: self._all)


class FakeSession:
    def __init__(self):
        self.execute = MagicMock(return_value=FakeResult())
        self.add = MagicMock()
        self.commit = MagicMock()
        self.delete = MagicMock()
        self.get = MagicMock()


class FakeDB:
    def __init__(self, session):
        self.session = session


def test_meal_plan_save_insert_and_update():
    from src.infrastructure.db.meal_plan_repository_impl import MealPlanRepositoryImpl
    from src.domain.models.daily_meal_plan import DailyMealPlan
    session = FakeSession()
    session.get.return_value = None  # first save -> insert
    repo = MealPlanRepositoryImpl(FakeDB(session), recipe_mapper=lambda x: None)
    plan = DailyMealPlan(uid='p1', user_uid='u1', date_=date.today())
    repo.save(plan)
    session.add.assert_called()
    session.commit.assert_called()
    # Update path
    session.get.return_value = SimpleNamespace(uid='p1')
    repo.save(plan)
    session.commit.assert_called()


def test_find_and_delete_and_get_all_and_dates_and_update():
    from src.infrastructure.db.meal_plan_repository_impl import MealPlanRepositoryImpl
    from src.domain.models.daily_meal_plan import DailyMealPlan
    from src.shared.exceptions.custom import MealPlanNotFoundException
    session = FakeSession()
    row = SimpleNamespace(uid='p1', user_uid='u1', date=date.today(),
                          breakfast_recipe=None, lunch_recipe=None, dinner_recipe=None, dessert_recipe=None)
    session.execute.side_effect = [
        FakeResult(scalar_one_or_none=row),             # find_by_user_and_date
        FakeResult(scalar_one_or_none=row),             # delete_by_user_and_date -> find
        FakeResult(scalars_all=[row]),                  # get_all_by_user
        FakeResult(scalars_all=[date.today(),]),        # get_all_dates_by_user
        FakeResult(scalar_one_or_none=row),             # update_by_user_and_date -> find
    ]
    repo = MealPlanRepositoryImpl(FakeDB(session), recipe_mapper=lambda x: None)
    found = repo.find_by_user_and_date('u1', date.today())
    assert isinstance(found, DailyMealPlan)
    repo.delete_by_user_and_date('u1', date.today())
    session.delete.assert_called()
    lst = repo.get_all_by_user('u1')
    assert len(lst) == 1
    dates = repo.get_all_dates_by_user('u1')
    assert isinstance(dates, list)
    # update by user/date
    repo.update_by_user_and_date(DailyMealPlan(uid='p1', user_uid='u1', date_=date.today()))
    session.commit.assert_called()
    # update raises when not found
    session.execute.side_effect = [FakeResult(scalar_one_or_none=None)]
    with pytest.raises(MealPlanNotFoundException):
        repo.update_by_user_and_date(DailyMealPlan(uid='p1', user_uid='u1', date_=date.today()))

