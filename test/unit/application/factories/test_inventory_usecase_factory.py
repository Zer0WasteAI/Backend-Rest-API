"""
Unit tests for Inventory Use Case Factory
Tests factory functions for inventory-related use cases
"""
import pytest
from unittest.mock import Mock, patch

from src.application.factories.inventory_usecase_factory import (
    make_add_ingredients_to_inventory_use_case,
    make_get_user_inventory_use_case,
    make_remove_ingredient_from_inventory_use_case,
    make_update_ingredient_quantity_use_case,
    make_get_expiring_soon_ingredients_use_case
)


class TestInventoryUseCaseFactory:
    """Test suite for Inventory Use Case Factory"""

    @patch('src.application.factories.inventory_usecase_factory.make_inventory_repository')
    @patch('src.application.factories.inventory_usecase_factory.make_inventory_calculator')
    def test_make_add_ingredients_to_inventory_use_case(self, mock_calculator, mock_repository):
        """Test add ingredients to inventory use case factory"""
        # Arrange
        mock_repository.return_value = Mock()
        mock_calculator.return_value = Mock()
        
        # Act
        result = make_add_ingredients_to_inventory_use_case()
        
        # Assert
        assert result is not None
        mock_repository.assert_called_once()
        mock_calculator.assert_called_once()

    @patch('src.application.factories.inventory_usecase_factory.make_inventory_repository')
    def test_make_get_user_inventory_use_case(self, mock_repository):
        """Test get user inventory use case factory"""
        # Arrange
        mock_repository.return_value = Mock()
        
        # Act
        result = make_get_user_inventory_use_case()
        
        # Assert
        assert result is not None
        mock_repository.assert_called_once()

    @patch('src.application.factories.inventory_usecase_factory.make_inventory_repository')
    def test_make_remove_ingredient_from_inventory_use_case(self, mock_repository):
        """Test remove ingredient from inventory use case factory"""
        # Arrange
        mock_repository.return_value = Mock()
        
        # Act
        result = make_remove_ingredient_from_inventory_use_case()
        
        # Assert
        assert result is not None
        mock_repository.assert_called_once()

    @patch('src.application.factories.inventory_usecase_factory.make_inventory_repository')
    def test_make_update_ingredient_quantity_use_case(self, mock_repository):
        """Test update ingredient quantity use case factory"""
        # Arrange
        mock_repository.return_value = Mock()
        
        # Act
        result = make_update_ingredient_quantity_use_case()
        
        # Assert
        assert result is not None
        mock_repository.assert_called_once()

    @patch('src.application.factories.inventory_usecase_factory.make_inventory_repository')
    def test_make_get_expiring_soon_ingredients_use_case(self, mock_repository):
        """Test get expiring soon ingredients use case factory"""
        # Arrange
        mock_repository.return_value = Mock()
        
        # Act
        result = make_get_expiring_soon_ingredients_use_case()
        
        # Assert
        assert result is not None
        mock_repository.assert_called_once()

    def test_factory_functions_exist(self):
        """Test that all factory functions are defined"""
        assert callable(make_add_ingredients_to_inventory_use_case)
        assert callable(make_get_user_inventory_use_case)
        assert callable(make_remove_ingredient_from_inventory_use_case)
        assert callable(make_update_ingredient_quantity_use_case)
        assert callable(make_get_expiring_soon_ingredients_use_case)

    @patch('src.application.factories.inventory_usecase_factory.make_inventory_repository')
    @patch('src.application.factories.inventory_usecase_factory.make_inventory_calculator')
    def test_make_add_ingredients_error_handling(self, mock_calculator, mock_repository):
        """Test add ingredients factory error handling"""
        # Arrange
        mock_repository.side_effect = Exception("Repository creation failed")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            make_add_ingredients_to_inventory_use_case()
        
        assert str(exc_info.value) == "Repository creation failed"

    @patch('src.application.factories.inventory_usecase_factory.make_inventory_repository')
    def test_make_get_user_inventory_error_handling(self, mock_repository):
        """Test get user inventory factory error handling"""
        # Arrange
        mock_repository.side_effect = Exception("Repository creation failed")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            make_get_user_inventory_use_case()
        
        assert str(exc_info.value) == "Repository creation failed"

    @patch('src.application.factories.inventory_usecase_factory.make_inventory_repository')
    def test_multiple_factory_calls_create_new_instances(self, mock_repository):
        """Test that multiple factory calls create new instances"""
        # Arrange
        mock_repository.return_value = Mock()
        
        # Act
        result1 = make_get_user_inventory_use_case()
        result2 = make_get_user_inventory_use_case()
        
        # Assert
        assert result1 is not None
        assert result2 is not None
        # Each call should create a new repository instance
        assert mock_repository.call_count == 2