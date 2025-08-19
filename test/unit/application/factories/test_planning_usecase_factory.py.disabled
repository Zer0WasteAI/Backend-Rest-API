"""
Unit tests for Planning Use Case Factory
Tests factory functions for meal planning-related use cases
"""
import pytest
from unittest.mock import Mock, patch

from src.application.factories.planning_usecase_factory import (
    make_create_meal_plan_use_case,
    make_get_meal_plan_use_case,
    make_update_meal_plan_use_case,
    make_delete_meal_plan_use_case,
    make_generate_shopping_list_use_case,
    make_suggest_recipes_for_plan_use_case
)


class TestPlanningUseCaseFactory:
    """Test suite for Planning Use Case Factory"""

    @patch('src.application.factories.planning_usecase_factory.make_meal_plan_repository')
    @patch('src.application.factories.planning_usecase_factory.make_recipe_repository')
    def test_make_create_meal_plan_use_case(self, mock_recipe_repo, mock_meal_plan_repo):
        """Test create meal plan use case factory"""
        # Arrange
        mock_meal_plan_repo.return_value = Mock()
        mock_recipe_repo.return_value = Mock()
        
        # Act
        result = make_create_meal_plan_use_case()
        
        # Assert
        assert result is not None
        mock_meal_plan_repo.assert_called_once()
        mock_recipe_repo.assert_called_once()

    @patch('src.application.factories.planning_usecase_factory.make_meal_plan_repository')
    def test_make_get_meal_plan_use_case(self, mock_meal_plan_repo):
        """Test get meal plan use case factory"""
        # Arrange
        mock_meal_plan_repo.return_value = Mock()
        
        # Act
        result = make_get_meal_plan_use_case()
        
        # Assert
        assert result is not None
        mock_meal_plan_repo.assert_called_once()

    @patch('src.application.factories.planning_usecase_factory.make_meal_plan_repository')
    @patch('src.application.factories.planning_usecase_factory.make_recipe_repository')
    def test_make_update_meal_plan_use_case(self, mock_recipe_repo, mock_meal_plan_repo):
        """Test update meal plan use case factory"""
        # Arrange
        mock_meal_plan_repo.return_value = Mock()
        mock_recipe_repo.return_value = Mock()
        
        # Act
        result = make_update_meal_plan_use_case()
        
        # Assert
        assert result is not None
        mock_meal_plan_repo.assert_called_once()
        mock_recipe_repo.assert_called_once()

    @patch('src.application.factories.planning_usecase_factory.make_meal_plan_repository')
    def test_make_delete_meal_plan_use_case(self, mock_meal_plan_repo):
        """Test delete meal plan use case factory"""
        # Arrange
        mock_meal_plan_repo.return_value = Mock()
        
        # Act
        result = make_delete_meal_plan_use_case()
        
        # Assert
        assert result is not None
        mock_meal_plan_repo.assert_called_once()

    @patch('src.application.factories.planning_usecase_factory.make_meal_plan_repository')
    @patch('src.application.factories.planning_usecase_factory.make_inventory_repository')
    def test_make_generate_shopping_list_use_case(self, mock_inventory_repo, mock_meal_plan_repo):
        """Test generate shopping list use case factory"""
        # Arrange
        mock_meal_plan_repo.return_value = Mock()
        mock_inventory_repo.return_value = Mock()
        
        # Act
        result = make_generate_shopping_list_use_case()
        
        # Assert
        assert result is not None
        mock_meal_plan_repo.assert_called_once()
        mock_inventory_repo.assert_called_once()

    @patch('src.application.factories.planning_usecase_factory.make_recipe_repository')
    @patch('src.application.factories.planning_usecase_factory.make_ai_adapter')
    def test_make_suggest_recipes_for_plan_use_case(self, mock_ai_adapter, mock_recipe_repo):
        """Test suggest recipes for plan use case factory"""
        # Arrange
        mock_recipe_repo.return_value = Mock()
        mock_ai_adapter.return_value = Mock()
        
        # Act
        result = make_suggest_recipes_for_plan_use_case()
        
        # Assert
        assert result is not None
        mock_recipe_repo.assert_called_once()
        mock_ai_adapter.assert_called_once()

    def test_factory_functions_exist(self):
        """Test that all factory functions are defined"""
        assert callable(make_create_meal_plan_use_case)
        assert callable(make_get_meal_plan_use_case)
        assert callable(make_update_meal_plan_use_case)
        assert callable(make_delete_meal_plan_use_case)
        assert callable(make_generate_shopping_list_use_case)
        assert callable(make_suggest_recipes_for_plan_use_case)

    @patch('src.application.factories.planning_usecase_factory.make_meal_plan_repository')
    @patch('src.application.factories.planning_usecase_factory.make_recipe_repository')
    def test_create_meal_plan_factory_error_handling(self, mock_recipe_repo, mock_meal_plan_repo):
        """Test create meal plan factory error handling"""
        # Arrange
        mock_meal_plan_repo.side_effect = Exception("Meal plan repository creation failed")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            make_create_meal_plan_use_case()
        
        assert str(exc_info.value) == "Meal plan repository creation failed"

    @patch('src.application.factories.planning_usecase_factory.make_recipe_repository')
    @patch('src.application.factories.planning_usecase_factory.make_ai_adapter')
    def test_suggest_recipes_ai_adapter_error_handling(self, mock_ai_adapter, mock_recipe_repo):
        """Test suggest recipes factory AI adapter error handling"""
        # Arrange
        mock_recipe_repo.return_value = Mock()
        mock_ai_adapter.side_effect = Exception("AI adapter creation failed")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            make_suggest_recipes_for_plan_use_case()
        
        assert str(exc_info.value) == "AI adapter creation failed"