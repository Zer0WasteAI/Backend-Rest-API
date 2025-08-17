import pytest
from unittest.mock import MagicMock, patch

from src.application.use_cases.recipes.generate_custom_recipe_use_case import GenerateCustomRecipeUseCase
from src.application.use_cases.recipes.get_saved_recipes_use_case import GetSavedRecipesUseCase
from src.application.use_cases.recipes.get_all_recipes_use_case import GetAllRecipesUseCase
from src.application.use_cases.recipes.delete_user_recipe_use_case import DeleteUserRecipeUseCase


@patch('src.application.use_cases.recipes.generate_custom_recipe_use_case.make_firestore_profile_service')
def test_generate_custom_recipe_combines_preferences(mock_fs_service):
    service = MagicMock()
    service.generate_recipes.return_value = {"generated_recipes": []}
    uc = GenerateCustomRecipeUseCase(service)
    mock_fs_service.return_value.get_profile.return_value = {
        'allergies': ['peanut'],
        'preferredFoodTypes': ['italian'],
        'specialDietItems': ['vegan'],
        'cookingLevel': 'intermediate',
    }
    res = uc.execute('u1', custom_ingredients=['Tomato', 'Peanut'], preferences=['low_salt'])
    # Ensure service is called and ingredients filtered
    args, kwargs = service.generate_recipes.call_args
    payload = args[0]
    ing_names = [i['name'].lower() for i in payload['ingredients']]
    assert 'peanut' not in ing_names
    assert 'tomato' in ing_names
    assert 'low_salt' in payload['preferences']
    assert 'italian' in payload['preferences']


def test_get_saved_recipes_use_case():
    repo = MagicMock()
    repo.get_all_by_user.return_value = []
    uc = GetSavedRecipesUseCase(repo)
    res = uc.execute('u1')
    assert res == []
    repo.get_all_by_user.assert_called_once_with('u1')


def test_get_all_recipes_use_case():
    repo = MagicMock()
    repo.get_all.return_value = []
    uc = GetAllRecipesUseCase(repo)
    res = uc.execute()
    assert res == []
    repo.get_all.assert_called_once()


def test_delete_user_recipe_use_case():
    repo = MagicMock()
    uc = DeleteUserRecipeUseCase(repo)
    uc.execute('u1', 'Title')
    repo.delete_by_user_and_title.assert_called_once_with('u1', 'Title')

