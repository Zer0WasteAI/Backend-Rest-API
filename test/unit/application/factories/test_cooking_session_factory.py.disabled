"""
Unit tests for Cooking Session Factory
Tests factory functions for cooking session-related use cases
"""
import pytest
from unittest.mock import Mock, patch

from src.application.factories.cooking_session_factory import (
    make_cooking_session_repository,
    make_ingredient_batch_repository,
    make_recipe_repository,
    make_mise_en_place_service,
    make_get_mise_en_place_use_case,
    make_start_cooking_session_use_case,
    make_complete_step_use_case,
    make_finish_cooking_session_use_case
)


class TestCookingSessionFactory:
    """Test suite for Cooking Session Factory"""

    @patch('src.application.factories.cooking_session_factory.db')
    def test_make_cooking_session_repository(self, mock_db):
        """Test cooking session repository factory"""
        # Act
        result = make_cooking_session_repository()
        
        # Assert
        assert result is not None

    @patch('src.application.factories.cooking_session_factory.db')
    def test_make_ingredient_batch_repository(self, mock_db):
        """Test ingredient batch repository factory"""
        # Act
        result = make_ingredient_batch_repository()
        
        # Assert
        assert result is not None

    @patch('src.application.factories.cooking_session_factory.db')
    def test_make_recipe_repository(self, mock_db):
        """Test recipe repository factory"""
        # Act
        result = make_recipe_repository()
        
        # Assert
        assert result is not None

    @patch('src.application.factories.cooking_session_factory.make_ingredient_batch_repository')
    def test_make_mise_en_place_service(self, mock_batch_repo):
        """Test mise en place service factory"""
        # Arrange
        mock_batch_repo.return_value = Mock()
        
        # Act
        result = make_mise_en_place_service()
        
        # Assert
        assert result is not None
        mock_batch_repo.assert_called_once()

    @patch('src.application.factories.cooking_session_factory.make_recipe_repository')
    @patch('src.application.factories.cooking_session_factory.make_ingredient_batch_repository')
    @patch('src.application.factories.cooking_session_factory.make_mise_en_place_service')
    def test_make_get_mise_en_place_use_case(self, mock_mise_service, mock_batch_repo, mock_recipe_repo):
        """Test get mise en place use case factory"""
        # Arrange
        mock_recipe_repo.return_value = Mock()
        mock_batch_repo.return_value = Mock()
        mock_mise_service.return_value = Mock()
        
        # Act
        result = make_get_mise_en_place_use_case()
        
        # Assert
        assert result is not None
        mock_recipe_repo.assert_called_once()
        mock_batch_repo.assert_called_once()
        mock_mise_service.assert_called_once()

    @patch('src.application.factories.cooking_session_factory.make_cooking_session_repository')
    @patch('src.application.factories.cooking_session_factory.make_recipe_repository')
    def test_make_start_cooking_session_use_case(self, mock_recipe_repo, mock_cooking_repo):
        """Test start cooking session use case factory"""
        # Arrange
        mock_cooking_repo.return_value = Mock()
        mock_recipe_repo.return_value = Mock()
        
        # Act
        result = make_start_cooking_session_use_case()
        
        # Assert
        assert result is not None
        mock_cooking_repo.assert_called_once()
        mock_recipe_repo.assert_called_once()

    @patch('src.application.factories.cooking_session_factory.make_cooking_session_repository')
    @patch('src.application.factories.cooking_session_factory.make_ingredient_batch_repository')
    def test_make_complete_step_use_case(self, mock_batch_repo, mock_cooking_repo):
        """Test complete step use case factory"""
        # Arrange
        mock_cooking_repo.return_value = Mock()
        mock_batch_repo.return_value = Mock()
        
        # Act
        result = make_complete_step_use_case()
        
        # Assert
        assert result is not None
        mock_cooking_repo.assert_called_once()
        mock_batch_repo.assert_called_once()

    @patch('src.application.factories.cooking_session_factory.make_cooking_session_repository')
    @patch('src.application.factories.environmental_savings_factory.make_estimate_savings_by_uid_use_case')
    def test_make_finish_cooking_session_use_case(self, mock_savings_use_case, mock_cooking_repo):
        """Test finish cooking session use case factory"""
        # Arrange
        mock_cooking_repo.return_value = Mock()
        mock_savings_use_case.return_value = Mock()
        
        # Act
        result = make_finish_cooking_session_use_case()
        
        # Assert
        assert result is not None
        mock_cooking_repo.assert_called_once()
        mock_savings_use_case.assert_called_once()

    def test_factory_functions_exist(self):
        """Test that all factory functions are defined"""
        assert callable(make_cooking_session_repository)
        assert callable(make_ingredient_batch_repository)
        assert callable(make_recipe_repository)
        assert callable(make_mise_en_place_service)
        assert callable(make_get_mise_en_place_use_case)
        assert callable(make_start_cooking_session_use_case)
        assert callable(make_complete_step_use_case)
        assert callable(make_finish_cooking_session_use_case)

    @patch('src.application.factories.cooking_session_factory.make_ingredient_batch_repository')
    def test_make_mise_en_place_service_error_handling(self, mock_batch_repo):
        """Test mise en place service factory error handling"""
        # Arrange
        mock_batch_repo.side_effect = Exception("Batch repository creation failed")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            make_mise_en_place_service()
        
        assert str(exc_info.value) == "Batch repository creation failed"

    @patch('src.application.factories.cooking_session_factory.make_recipe_repository')
    @patch('src.application.factories.cooking_session_factory.make_ingredient_batch_repository')
    @patch('src.application.factories.cooking_session_factory.make_mise_en_place_service')
    def test_get_mise_en_place_use_case_error_handling(self, mock_mise_service, mock_batch_repo, mock_recipe_repo):
        """Test get mise en place use case factory error handling"""
        # Arrange
        mock_recipe_repo.side_effect = Exception("Recipe repository creation failed")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            make_get_mise_en_place_use_case()
        
        assert str(exc_info.value) == "Recipe repository creation failed"