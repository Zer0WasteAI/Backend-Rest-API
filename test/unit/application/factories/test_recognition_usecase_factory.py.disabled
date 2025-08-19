"""
Unit tests for Recognition Use Case Factory
Tests factory functions for food recognition-related use cases
"""
import pytest
from unittest.mock import Mock, patch

from src.application.factories.recognition_usecase_factory import (
    make_recognize_food_use_case,
    make_recognize_ingredients_use_case,
    make_analyze_food_nutrition_use_case,
    make_hybrid_recognition_use_case
)


class TestRecognitionUseCaseFactory:
    """Test suite for Recognition Use Case Factory"""

    @patch('src.application.factories.recognition_usecase_factory.make_ai_adapter')
    @patch('src.application.factories.recognition_usecase_factory.make_image_processor')
    def test_make_recognize_food_use_case(self, mock_image_processor, mock_ai_adapter):
        """Test recognize food use case factory"""
        # Arrange
        mock_ai_adapter.return_value = Mock()
        mock_image_processor.return_value = Mock()
        
        # Act
        result = make_recognize_food_use_case()
        
        # Assert
        assert result is not None
        mock_ai_adapter.assert_called_once()
        mock_image_processor.assert_called_once()

    @patch('src.application.factories.recognition_usecase_factory.make_ai_adapter')
    @patch('src.application.factories.recognition_usecase_factory.make_image_processor')
    def test_make_recognize_ingredients_use_case(self, mock_image_processor, mock_ai_adapter):
        """Test recognize ingredients use case factory"""
        # Arrange
        mock_ai_adapter.return_value = Mock()
        mock_image_processor.return_value = Mock()
        
        # Act
        result = make_recognize_ingredients_use_case()
        
        # Assert
        assert result is not None
        mock_ai_adapter.assert_called_once()
        mock_image_processor.assert_called_once()

    @patch('src.application.factories.recognition_usecase_factory.make_ai_adapter')
    def test_make_analyze_food_nutrition_use_case(self, mock_ai_adapter):
        """Test analyze food nutrition use case factory"""
        # Arrange
        mock_ai_adapter.return_value = Mock()
        
        # Act
        result = make_analyze_food_nutrition_use_case()
        
        # Assert
        assert result is not None
        mock_ai_adapter.assert_called_once()

    @patch('src.application.factories.recognition_usecase_factory.make_ai_adapter')
    @patch('src.application.factories.recognition_usecase_factory.make_image_processor')
    @patch('src.application.factories.recognition_usecase_factory.make_food_vision_service')
    def test_make_hybrid_recognition_use_case(self, mock_vision_service, mock_image_processor, mock_ai_adapter):
        """Test hybrid recognition use case factory"""
        # Arrange
        mock_ai_adapter.return_value = Mock()
        mock_image_processor.return_value = Mock()
        mock_vision_service.return_value = Mock()
        
        # Act
        result = make_hybrid_recognition_use_case()
        
        # Assert
        assert result is not None
        mock_ai_adapter.assert_called_once()
        mock_image_processor.assert_called_once()
        mock_vision_service.assert_called_once()

    def test_factory_functions_exist(self):
        """Test that all factory functions are defined"""
        assert callable(make_recognize_food_use_case)
        assert callable(make_recognize_ingredients_use_case)
        assert callable(make_analyze_food_nutrition_use_case)
        assert callable(make_hybrid_recognition_use_case)

    @patch('src.application.factories.recognition_usecase_factory.make_ai_adapter')
    @patch('src.application.factories.recognition_usecase_factory.make_image_processor')
    def test_recognize_food_factory_error_handling(self, mock_image_processor, mock_ai_adapter):
        """Test recognize food factory error handling"""
        # Arrange
        mock_ai_adapter.side_effect = Exception("AI adapter creation failed")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            make_recognize_food_use_case()
        
        assert str(exc_info.value) == "AI adapter creation failed"

    @patch('src.application.factories.recognition_usecase_factory.make_ai_adapter')
    @patch('src.application.factories.recognition_usecase_factory.make_image_processor')
    def test_recognize_ingredients_image_processor_error_handling(self, mock_image_processor, mock_ai_adapter):
        """Test recognize ingredients factory image processor error handling"""
        # Arrange
        mock_ai_adapter.return_value = Mock()
        mock_image_processor.side_effect = Exception("Image processor creation failed")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            make_recognize_ingredients_use_case()
        
        assert str(exc_info.value) == "Image processor creation failed"

    @patch('src.application.factories.recognition_usecase_factory.make_ai_adapter')
    def test_analyze_nutrition_factory_error_handling(self, mock_ai_adapter):
        """Test analyze nutrition factory error handling"""
        # Arrange
        mock_ai_adapter.side_effect = Exception("AI adapter creation failed")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            make_analyze_food_nutrition_use_case()
        
        assert str(exc_info.value) == "AI adapter creation failed"

    @patch('src.application.factories.recognition_usecase_factory.make_ai_adapter')
    @patch('src.application.factories.recognition_usecase_factory.make_image_processor')
    @patch('src.application.factories.recognition_usecase_factory.make_food_vision_service')
    def test_hybrid_recognition_vision_service_error_handling(self, mock_vision_service, mock_image_processor, mock_ai_adapter):
        """Test hybrid recognition factory vision service error handling"""
        # Arrange
        mock_ai_adapter.return_value = Mock()
        mock_image_processor.return_value = Mock()
        mock_vision_service.side_effect = Exception("Vision service creation failed")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            make_hybrid_recognition_use_case()
        
        assert str(exc_info.value) == "Vision service creation failed"