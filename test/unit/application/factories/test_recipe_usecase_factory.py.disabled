"""
Unit tests for Recipe Use Case Factory
Tests factory functions for recipe-related use cases
"""
import pytest
from unittest.mock import Mock, patch

from src.application.factories.recipe_usecase_factory import (
    make_save_recipe_use_case,
    make_get_recipe_by_uid_use_case,
    make_get_recipes_by_user_use_case,
    make_update_recipe_use_case,
    make_delete_recipe_use_case,
    make_search_recipes_use_case,
    make_get_recipe_nutrition_use_case,
    make_favorite_recipe_use_case,
    make_get_favorite_recipes_use_case
)


class TestRecipeUseCaseFactory:
    """Test suite for Recipe Use Case Factory"""

    @patch('src.application.factories.recipe_usecase_factory.make_recipe_repository')
    def test_make_save_recipe_use_case(self, mock_repository):
        """Test save recipe use case factory"""
        # Arrange
        mock_repository.return_value = Mock()
        
        # Act
        result = make_save_recipe_use_case()
        
        # Assert
        assert result is not None
        mock_repository.assert_called_once()

    @patch('src.application.factories.recipe_usecase_factory.make_recipe_repository')
    def test_make_get_recipe_by_uid_use_case(self, mock_repository):
        """Test get recipe by uid use case factory"""
        # Arrange
        mock_repository.return_value = Mock()
        
        # Act
        result = make_get_recipe_by_uid_use_case()
        
        # Assert
        assert result is not None
        mock_repository.assert_called_once()

    @patch('src.application.factories.recipe_usecase_factory.make_recipe_repository')
    def test_make_get_recipes_by_user_use_case(self, mock_repository):
        """Test get recipes by user use case factory"""
        # Arrange
        mock_repository.return_value = Mock()
        
        # Act
        result = make_get_recipes_by_user_use_case()
        
        # Assert
        assert result is not None
        mock_repository.assert_called_once()

    @patch('src.application.factories.recipe_usecase_factory.make_recipe_repository')
    def test_make_update_recipe_use_case(self, mock_repository):
        """Test update recipe use case factory"""
        # Arrange
        mock_repository.return_value = Mock()
        
        # Act
        result = make_update_recipe_use_case()
        
        # Assert
        assert result is not None
        mock_repository.assert_called_once()

    @patch('src.application.factories.recipe_usecase_factory.make_delete_recipe_use_case')
    def test_make_delete_recipe_use_case(self, mock_factory):
        """Test delete recipe use case factory"""
        # Arrange
        mock_factory.return_value = Mock()
        
        # Act
        result = make_delete_recipe_use_case()
        
        # Assert
        assert result is not None
        mock_factory.assert_called_once()

    @patch('src.application.factories.recipe_usecase_factory.make_recipe_repository')
    def test_make_search_recipes_use_case(self, mock_repository):
        """Test search recipes use case factory"""
        # Arrange
        mock_repository.return_value = Mock()
        
        # Act
        result = make_search_recipes_use_case()
        
        # Assert
        assert result is not None
        mock_repository.assert_called_once()

    @patch('src.application.factories.recipe_usecase_factory.make_recipe_repository')
    @patch('src.application.factories.recipe_usecase_factory.make_ai_adapter')
    def test_make_get_recipe_nutrition_use_case(self, mock_ai_adapter, mock_repository):
        """Test get recipe nutrition use case factory"""
        # Arrange
        mock_repository.return_value = Mock()
        mock_ai_adapter.return_value = Mock()
        
        # Act
        result = make_get_recipe_nutrition_use_case()
        
        # Assert
        assert result is not None
        mock_repository.assert_called_once()
        mock_ai_adapter.assert_called_once()

    @patch('src.application.factories.recipe_usecase_factory.make_recipe_repository')
    def test_make_favorite_recipe_use_case(self, mock_repository):
        """Test favorite recipe use case factory"""
        # Arrange
        mock_repository.return_value = Mock()
        
        # Act
        result = make_favorite_recipe_use_case()
        
        # Assert
        assert result is not None
        mock_repository.assert_called_once()

    @patch('src.application.factories.recipe_usecase_factory.make_recipe_repository')
    def test_make_get_favorite_recipes_use_case(self, mock_repository):
        """Test get favorite recipes use case factory"""
        # Arrange
        mock_repository.return_value = Mock()
        
        # Act
        result = make_get_favorite_recipes_use_case()
        
        # Assert
        assert result is not None
        mock_repository.assert_called_once()

    def test_factory_functions_exist(self):
        """Test that all factory functions are defined"""
        assert callable(make_save_recipe_use_case)
        assert callable(make_get_recipe_by_uid_use_case)
        assert callable(make_get_recipes_by_user_use_case)
        assert callable(make_update_recipe_use_case)
        assert callable(make_delete_recipe_use_case)
        assert callable(make_search_recipes_use_case)
        assert callable(make_get_recipe_nutrition_use_case)
        assert callable(make_favorite_recipe_use_case)
        assert callable(make_get_favorite_recipes_use_case)

    @patch('src.application.factories.recipe_usecase_factory.make_recipe_repository')
    def test_save_recipe_factory_error_handling(self, mock_repository):
        """Test save recipe factory error handling"""
        # Arrange
        mock_repository.side_effect = Exception("Repository creation failed")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            make_save_recipe_use_case()
        
        assert str(exc_info.value) == "Repository creation failed"

    @patch('src.application.factories.recipe_usecase_factory.make_recipe_repository')
    @patch('src.application.factories.recipe_usecase_factory.make_ai_adapter')
    def test_nutrition_factory_ai_adapter_error_handling(self, mock_ai_adapter, mock_repository):
        """Test nutrition factory AI adapter error handling"""
        # Arrange
        mock_repository.return_value = Mock()
        mock_ai_adapter.side_effect = Exception("AI adapter creation failed")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            make_get_recipe_nutrition_use_case()
        
        assert str(exc_info.value) == "AI adapter creation failed"