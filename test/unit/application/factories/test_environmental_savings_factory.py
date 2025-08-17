"""
Unit tests for Environmental Savings Factory
Tests factory functions for environmental savings calculations
"""
import pytest
from unittest.mock import Mock, patch

from src.application.factories.environmental_savings_factory import (
    make_estimate_savings_by_uid_use_case
)


class TestEnvironmentalSavingsFactory:
    """Test suite for Environmental Savings Factory"""

    @patch('src.application.factories.environmental_savings_factory.make_recipe_repository')
    @patch('src.application.factories.environmental_savings_factory.make_ai_adapter')
    @patch('src.application.factories.environmental_savings_factory.make_environmental_savings_repository')
    def test_make_estimate_savings_by_uid_use_case(self, mock_savings_repo, mock_ai_adapter, mock_recipe_repo):
        """Test estimate savings by uid use case factory"""
        # Arrange
        mock_recipe_repo.return_value = Mock()
        mock_ai_adapter.return_value = Mock()
        mock_savings_repo.return_value = Mock()
        
        # Act
        result = make_estimate_savings_by_uid_use_case()
        
        # Assert
        assert result is not None
        mock_recipe_repo.assert_called_once()
        mock_ai_adapter.assert_called_once()
        mock_savings_repo.assert_called_once()

    def test_factory_function_exists(self):
        """Test that factory function is defined"""
        assert callable(make_estimate_savings_by_uid_use_case)

    @patch('src.application.factories.environmental_savings_factory.make_recipe_repository')
    @patch('src.application.factories.environmental_savings_factory.make_ai_adapter')
    @patch('src.application.factories.environmental_savings_factory.make_environmental_savings_repository')
    def test_estimate_savings_factory_error_handling(self, mock_savings_repo, mock_ai_adapter, mock_recipe_repo):
        """Test estimate savings factory error handling"""
        # Arrange
        mock_recipe_repo.side_effect = Exception("Recipe repository creation failed")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            make_estimate_savings_by_uid_use_case()
        
        assert str(exc_info.value) == "Recipe repository creation failed"

    @patch('src.application.factories.environmental_savings_factory.make_recipe_repository')
    @patch('src.application.factories.environmental_savings_factory.make_ai_adapter')
    @patch('src.application.factories.environmental_savings_factory.make_environmental_savings_repository')
    def test_estimate_savings_ai_adapter_error_handling(self, mock_savings_repo, mock_ai_adapter, mock_recipe_repo):
        """Test estimate savings factory AI adapter error handling"""
        # Arrange
        mock_recipe_repo.return_value = Mock()
        mock_ai_adapter.side_effect = Exception("AI adapter creation failed")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            make_estimate_savings_by_uid_use_case()
        
        assert str(exc_info.value) == "AI adapter creation failed"

    @patch('src.application.factories.environmental_savings_factory.make_recipe_repository')
    @patch('src.application.factories.environmental_savings_factory.make_ai_adapter')
    @patch('src.application.factories.environmental_savings_factory.make_environmental_savings_repository')
    def test_estimate_savings_repository_error_handling(self, mock_savings_repo, mock_ai_adapter, mock_recipe_repo):
        """Test estimate savings factory repository error handling"""
        # Arrange
        mock_recipe_repo.return_value = Mock()
        mock_ai_adapter.return_value = Mock()
        mock_savings_repo.side_effect = Exception("Savings repository creation failed")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            make_estimate_savings_by_uid_use_case()
        
        assert str(exc_info.value) == "Savings repository creation failed"

    @patch('src.application.factories.environmental_savings_factory.make_recipe_repository')
    @patch('src.application.factories.environmental_savings_factory.make_ai_adapter')
    @patch('src.application.factories.environmental_savings_factory.make_environmental_savings_repository')
    def test_multiple_factory_calls_create_new_instances(self, mock_savings_repo, mock_ai_adapter, mock_recipe_repo):
        """Test that multiple factory calls create new instances"""
        # Arrange
        mock_recipe_repo.return_value = Mock()
        mock_ai_adapter.return_value = Mock()
        mock_savings_repo.return_value = Mock()
        
        # Act
        result1 = make_estimate_savings_by_uid_use_case()
        result2 = make_estimate_savings_by_uid_use_case()
        
        # Assert
        assert result1 is not None
        assert result2 is not None
        # Each call should create new repository instances
        assert mock_recipe_repo.call_count == 2
        assert mock_ai_adapter.call_count == 2
        assert mock_savings_repo.call_count == 2