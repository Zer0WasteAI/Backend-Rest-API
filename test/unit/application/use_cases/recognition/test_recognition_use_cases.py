"""
Unit tests for Recognition Use Cases
Tests recognition business logic and AI integration
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.application.use_cases.recognition.recognize_ingredients_complete_use_case import RecognizeIngredientsCompleteUseCase
from src.application.use_cases.recognition.recognize_ingredients_use_case import RecognizeIngredientsUseCase
from src.application.use_cases.recognition.recognize_foods_use_case import RecognizeFoodsUseCase
from src.application.use_cases.recognition.recognize_batch_use_case import RecognizeBatchUseCase


class TestRecognitionUseCases:
    """Test suite for Recognition Use Cases"""

    def test_recognize_ingredients_complete_use_case(self):
        """Test RecognizeIngredientsCompleteUseCase execution"""
        # Arrange
        mock_ai_service = Mock()
        mock_recognition_repo = Mock()
        mock_storage_adapter = Mock()
        mock_calculator = Mock()
        
        mock_ai_service.recognize_ingredients.return_value = {
            "ingredients": [
                {"name": "Tomate", "confidence": 0.95, "quantity": "3 piezas"},
                {"name": "Cebolla", "confidence": 0.87, "quantity": "2 piezas"}
            ]
        }
        
        mock_recognition_repo.save.return_value = "recognition_123"
        
        use_case = RecognizeIngredientsCompleteUseCase(
            ai_service=mock_ai_service,
            recognition_repository=mock_recognition_repo,
            storage_adapter=mock_storage_adapter,
            calculator_service=mock_calculator
        )
        
        # Act
        result = use_case.execute(
            user_uid="user_123",
            images_paths=["path1.jpg", "path2.jpg"]
        )
        
        # Assert
        assert "recognition_id" in result
        assert "ingredients" in result
        mock_ai_service.recognize_ingredients.assert_called_once()
        mock_recognition_repo.save.assert_called_once()

    def test_recognize_ingredients_use_case_success(self):
        """Test basic ingredient recognition success"""
        # Arrange
        mock_ai_service = Mock()
        mock_recognition_repo = Mock()
        mock_storage_adapter = Mock()
        mock_calculator = Mock()
        
        mock_ai_service.recognize_ingredients.return_value = {
            "ingredients": [{"name": "Apple", "confidence": 0.92}]
        }
        
        use_case = RecognizeIngredientsUseCase(
            ai_service=mock_ai_service,
            recognition_repository=mock_recognition_repo,
            storage_adapter=mock_storage_adapter,
            calculator_service=mock_calculator
        )
        
        # Act
        result = use_case.execute("user_123", ["apple.jpg"])
        
        # Assert
        assert "ingredients" in result
        mock_ai_service.recognize_ingredients.assert_called_once()

    def test_recognize_foods_use_case_success(self):
        """Test food recognition use case"""
        # Arrange
        mock_ai_service = Mock()
        mock_recognition_repo = Mock()
        mock_storage_adapter = Mock()
        mock_calculator = Mock()
        
        mock_ai_service.recognize_foods.return_value = {
            "foods": [{"name": "Bread", "confidence": 0.89, "expiry_estimate": "2024-01-20"}]
        }
        
        use_case = RecognizeFoodsUseCase(
            ai_service=mock_ai_service,
            recognition_repository=mock_recognition_repo,
            storage_adapter=mock_storage_adapter,
            calculator_service=mock_calculator
        )
        
        # Act
        result = use_case.execute("user_123", ["bread.jpg"])
        
        # Assert
        assert "foods" in result
        mock_ai_service.recognize_foods.assert_called_once()

    def test_recognize_batch_use_case_success(self):
        """Test batch recognition use case"""
        # Arrange
        mock_ai_service = Mock()
        mock_recognition_repo = Mock()
        mock_storage_adapter = Mock()
        mock_calculator = Mock()
        
        mock_ai_service.recognize_batch.return_value = {
            "batch_results": [
                {"image": "img1.jpg", "items": [{"name": "Tomato", "confidence": 0.95}]},
                {"image": "img2.jpg", "items": [{"name": "Onion", "confidence": 0.88}]}
            ]
        }
        
        use_case = RecognizeBatchUseCase(
            ai_service=mock_ai_service,
            recognition_repository=mock_recognition_repo,
            storage_adapter=mock_storage_adapter,
            calculator_service=mock_calculator
        )
        
        # Act
        result = use_case.execute("user_123", ["img1.jpg", "img2.jpg"])
        
        # Assert
        assert "batch_results" in result
        mock_ai_service.recognize_batch.assert_called_once()

    def test_recognition_with_empty_images_list(self):
        """Test recognition with empty images list"""
        # Arrange
        mock_ai_service = Mock()
        mock_recognition_repo = Mock()
        mock_storage_adapter = Mock()
        mock_calculator = Mock()
        
        use_case = RecognizeIngredientsUseCase(
            ai_service=mock_ai_service,
            recognition_repository=mock_recognition_repo,
            storage_adapter=mock_storage_adapter,
            calculator_service=mock_calculator
        )
        
        # Act & Assert
        with pytest.raises(Exception):
            use_case.execute("user_123", [])

    def test_recognition_with_ai_service_failure(self):
        """Test recognition when AI service fails"""
        # Arrange
        mock_ai_service = Mock()
        mock_recognition_repo = Mock()
        mock_storage_adapter = Mock()
        mock_calculator = Mock()
        
        mock_ai_service.recognize_ingredients.side_effect = Exception("AI Service Error")
        
        use_case = RecognizeIngredientsUseCase(
            ai_service=mock_ai_service,
            recognition_repository=mock_recognition_repo,
            storage_adapter=mock_storage_adapter,
            calculator_service=mock_calculator
        )
        
        # Act & Assert
        with pytest.raises(Exception):
            use_case.execute("user_123", ["test.jpg"])

    def test_recognition_confidence_filtering(self):
        """Test that low confidence results are handled appropriately"""
        # Arrange
        mock_ai_service = Mock()
        mock_recognition_repo = Mock()
        mock_storage_adapter = Mock()
        mock_calculator = Mock()
        
        mock_ai_service.recognize_ingredients.return_value = {
            "ingredients": [
                {"name": "High Confidence Item", "confidence": 0.95},
                {"name": "Low Confidence Item", "confidence": 0.45},
                {"name": "Medium Confidence Item", "confidence": 0.75}
            ]
        }
        
        use_case = RecognizeIngredientsUseCase(
            ai_service=mock_ai_service,
            recognition_repository=mock_recognition_repo,
            storage_adapter=mock_storage_adapter,
            calculator_service=mock_calculator
        )
        
        # Act
        result = use_case.execute("user_123", ["mixed_confidence.jpg"])
        
        # Assert
        assert len(result["ingredients"]) == 3  # Should include all items but with confidence scores
        mock_ai_service.recognize_ingredients.assert_called_once()

    def test_recognition_repository_integration(self):
        """Test that recognition results are properly saved to repository"""
        # Arrange
        mock_ai_service = Mock()
        mock_recognition_repo = Mock()
        mock_storage_adapter = Mock()
        mock_calculator = Mock()
        
        mock_ai_service.recognize_ingredients.return_value = {"ingredients": []}
        mock_recognition_repo.save.return_value = "rec_456"
        
        use_case = RecognizeIngredientsCompleteUseCase(
            ai_service=mock_ai_service,
            recognition_repository=mock_recognition_repo,
            storage_adapter=mock_storage_adapter,
            calculator_service=mock_calculator
        )
        
        # Act
        result = use_case.execute("user_123", ["test.jpg"])
        
        # Assert
        mock_recognition_repo.save.assert_called_once()
        # Verify the recognition object passed to save has correct structure
        saved_recognition = mock_recognition_repo.save.call_args[0][0]
        assert saved_recognition.user_uid == "user_123"
        assert saved_recognition.images_paths == ["test.jpg"]
