import pytest
from unittest.mock import MagicMock, patch

from src.application.use_cases.recipes.add_recipe_to_favorites_use_case import AddRecipeToFavoritesUseCase
from src.application.use_cases.recipes.remove_recipe_from_favorites_use_case import RemoveRecipeFromFavoritesUseCase
from src.application.use_cases.recipes.get_favorite_recipes_use_case import GetFavoriteRecipesUseCase
from src.application.use_cases.recipes.get_mise_en_place_use_case import GetMiseEnPlaceUseCase
from src.shared.exceptions.custom import UserNotFoundException, RecipeNotFoundException


@patch('src.application.use_cases.recipes.add_recipe_to_favorites_use_case.db')
def test_add_recipe_to_favorites_success(mock_db):
    user_repo = MagicMock()
    recipe_repo = MagicMock()
    user = MagicMock()
    user.favorite_recipes = []
    user_repo.find_by_uid.return_value = user
    recipe_orm = MagicMock()
    recipe_repo.find_orm_by_id.return_value = recipe_orm
    uc = AddRecipeToFavoritesUseCase(user_repo, recipe_repo)
    uc.execute('u1', 'r1')
    assert recipe_orm in user.favorite_recipes
    assert mock_db.session.commit.called


@patch('src.application.use_cases.recipes.remove_recipe_from_favorites_use_case.db')
def test_remove_recipe_from_favorites_success(mock_db):
    user_repo = MagicMock()
    recipe_repo = MagicMock()
    user = MagicMock()
    # simulate relationship .all() returning list with recipe
    recipe_orm = MagicMock()
    user.favorite_recipes.all.return_value = [recipe_orm]
    user_repo.find_by_uid.return_value = user
    recipe_repo.find_orm_by_id.return_value = recipe_orm
    uc = RemoveRecipeFromFavoritesUseCase(user_repo, recipe_repo)
    uc.execute('u1', 'r1')
    assert user.favorite_recipes.remove.called
    assert mock_db.session.commit.called


def test_get_favorite_recipes_maps_to_domain():
    user_repo = MagicMock()
    recipe_repo = MagicMock()
    user = MagicMock()
    recipe_orm = MagicMock()
    user.favorite_recipes.all.return_value = [recipe_orm]
    user_repo.find_by_uid.return_value = user
    recipe_repo.map_to_domain.return_value = MagicMock()
    uc = GetFavoriteRecipesUseCase(user_repo, recipe_repo)
    res = uc.execute('u1')
    assert len(res) == 1
    recipe_repo.map_to_domain.assert_called_once_with(recipe_orm)


def test_get_favorite_recipes_user_not_found():
    user_repo = MagicMock()
    recipe_repo = MagicMock()
    user_repo.find_by_uid.return_value = None
    uc = GetFavoriteRecipesUseCase(user_repo, recipe_repo)
    with pytest.raises(UserNotFoundException):
        uc.execute('u1')


def test_get_mise_en_place_success():
    recipe_repo = MagicMock()
    batch_repo = MagicMock()
    mise_service = MagicMock()
    recipe_repo.find_by_uid.return_value = MagicMock()
    mise = MagicMock()
    mise_service.generate_mise_en_place.return_value = mise
    uc = GetMiseEnPlaceUseCase(recipe_repo, batch_repo, mise_service)
    res = uc.execute('r1', servings=2, user_uid='u1')
    assert res == mise


def test_get_mise_en_place_invalid_servings():
    uc = GetMiseEnPlaceUseCase(MagicMock(), MagicMock(), MagicMock())
    with pytest.raises(ValueError):
        uc.execute('r1', servings=0, user_uid='u1')


def test_get_mise_en_place_recipe_not_found():
    recipe_repo = MagicMock()
    recipe_repo.find_by_uid.return_value = None
    uc = GetMiseEnPlaceUseCase(recipe_repo, MagicMock(), MagicMock())
    with pytest.raises(RecipeNotFoundException):
        uc.execute('r1', servings=1, user_uid='u1')

