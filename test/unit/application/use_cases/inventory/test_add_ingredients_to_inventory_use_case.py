"""
Unit tests for Add Ingredients to Inventory Use Case
Tests ingredient addition functionality with validation and AI enrichment
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from src.application.use_cases.inventory.add_ingredients_to_inventory_use_case import AddIngredientsToInventoryUseCase


class TestAddIngredientsToInventoryUseCase:
    """Test suite for Add Ingredients to Inventory Use Case"""
    
    @pytest.fixture
    def mock_repository(self):
        """Mock inventory repository"""
        return Mock()
    
    @pytest.fixture
    def mock_calculator(self):
        """Mock inventory calculator"""
        return Mock()
    
    @pytest.fixture
    def mock_ai_service(self):
        """Mock AI service for enrichment"""
        return Mock()
    
    @pytest.fixture
    def mock_image_generator_service(self):
        """Mock image generator service"""
        return Mock()
    
    @pytest.fixture
    def use_case(self, mock_repository, mock_calculator):
        """Create use case with basic mocked dependencies"""
        return AddIngredientsToInventoryUseCase(
            repository=mock_repository,
            calculator=mock_calculator
        )
    
    @pytest.fixture
    def use_case_with_ai(self, mock_repository, mock_calculator, 
                        mock_ai_service, mock_image_generator_service):
        """Create use case with AI services"""
        return AddIngredientsToInventoryUseCase(
            repository=mock_repository,
            calculator=mock_calculator,
            ai_service=mock_ai_service,
            ingredient_image_generator_service=mock_image_generator_service
        )
    
    @pytest.fixture
    def sample_ingredients_data(self):
        """Sample ingredients data for testing"""
        return [
            {
                "name": "Tomate",
                "type_unit": "piezas",
                "storage_type": "refrigerador",
                "tips": "Mantener a temperatura ambiente",
                "image_path": "https://example.com/tomate.jpg",
                "quantity": 5,
                "expiration_time": 7,
                "time_unit": "days"
            },
            {
                "name": "Cebolla",
                "type_unit": "gr",
                "storage_type": "despensa",
                "tips": "Lugar seco y ventilado",
                "image_path": "https://example.com/cebolla.jpg",
                "quantity": 500,
                "expiration_time": 2,
                "time_unit": "weeks"
            }
        ]

    def test_add_ingredients_with_existing_inventory(self, use_case, mock_repository, 
                                                   mock_calculator, sample_ingredients_data):
        """Test adding ingredients to existing inventory"""
        # Arrange
        mock_inventory = Mock()
        mock_repository.get_inventory.return_value = mock_inventory
        mock_calculator.calculate_expiration_date.return_value = datetime(2024, 1, 27)
        
        # Act
        use_case.execute("user_123", sample_ingredients_data)
        
        # Assert
        mock_repository.get_inventory.assert_called_once_with("user_123")
        mock_repository.create_inventory.assert_not_called()  # Should not create new inventory
        assert mock_repository.add_ingredient_stack.call_count == 2

    def test_add_ingredients_with_new_inventory(self, use_case, mock_repository, 
                                              mock_calculator, sample_ingredients_data):
        """Test adding ingredients when no inventory exists"""
        # Arrange
        mock_repository.get_inventory.return_value = None  # No existing inventory
        mock_calculator.calculate_expiration_date.return_value = datetime(2024, 1, 27)
        
        # Act
        use_case.execute("user_123", sample_ingredients_data)
        
        # Assert
        mock_repository.get_inventory.assert_called_once_with("user_123")
        mock_repository.create_inventory.assert_called_once_with("user_123")
        assert mock_repository.add_ingredient_stack.call_count == 2

    def test_add_ingredients_with_ai_enrichment(self, use_case_with_ai, mock_repository,
                                               mock_calculator, mock_ai_service,
                                               sample_ingredients_data):
        """Test adding ingredients with AI enrichment"""
        # Arrange
        mock_inventory = Mock()
        mock_repository.get_inventory.return_value = mock_inventory
        mock_calculator.calculate_expiration_date.return_value = datetime(2024, 1, 27)
        
        # Mock AI service response
        mock_ai_service.enrich_ingredient_data.return_value = {
            "environmental_impact": {"co2_footprint": 0.1},
            "utilization_ideas": ["En ensaladas", "Salsa de tomate"]
        }
        
        # Act
        use_case_with_ai.execute("user_123", sample_ingredients_data)
        
        # Assert
        # AI service should be called for enrichment
        assert mock_ai_service.enrich_ingredient_data.call_count >= 1

    def test_add_ingredients_with_image_recovery(self, use_case_with_ai, mock_repository,
                                               mock_calculator, mock_image_generator_service,
                                               sample_ingredients_data):
        """Test adding ingredients with image recovery"""
        # Arrange
        mock_inventory = Mock()
        mock_repository.get_inventory.return_value = mock_inventory
        mock_calculator.calculate_expiration_date.return_value = datetime(2024, 1, 27)
        
        # Act
        use_case_with_ai.execute("user_123", sample_ingredients_data)
        
        # Assert
        # Image recovery should be attempted
        assert mock_image_generator_service.method_calls

    def test_add_ingredients_empty_list(self, use_case, mock_repository):
        """Test adding empty ingredients list"""
        # Arrange
        mock_inventory = Mock()
        mock_repository.get_inventory.return_value = mock_inventory
        
        # Act
        use_case.execute("user_123", [])
        
        # Assert
        mock_repository.get_inventory.assert_called_once_with("user_123")
        mock_repository.add_ingredient_stack.assert_not_called()

    def test_add_ingredients_invalid_ingredient_data(self, use_case, mock_repository, mock_calculator):
        """Test adding ingredients with invalid data"""
        # Arrange
        mock_inventory = Mock()
        mock_repository.get_inventory.return_value = mock_inventory
        
        invalid_ingredients = [
            {
                "name": "Tomate",
                # Missing required fields
            }
        ]
        
        # Act & Assert
        with pytest.raises(KeyError):
            use_case.execute("user_123", invalid_ingredients)

    def test_add_ingredients_repository_error_propagates(self, use_case, mock_repository):
        """Test that repository errors are propagated"""
        # Arrange
        mock_repository.get_inventory.side_effect = Exception("Database connection error")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            use_case.execute("user_123", [])
        
        assert str(exc_info.value) == "Database connection error"

    def test_add_ingredients_calculator_error_handling(self, use_case, mock_repository, 
                                                     mock_calculator, sample_ingredients_data):
        """Test handling of calculator errors"""
        # Arrange
        mock_inventory = Mock()
        mock_repository.get_inventory.return_value = mock_inventory
        mock_calculator.calculate_expiration_date.side_effect = Exception("Calculation error")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            use_case.execute("user_123", sample_ingredients_data)
        
        assert str(exc_info.value) == "Calculation error"

    def test_add_ingredients_ai_service_error_handling(self, use_case_with_ai, mock_repository,
                                                      mock_calculator, mock_ai_service,
                                                      sample_ingredients_data):
        """Test handling of AI service errors"""
        # Arrange
        mock_inventory = Mock()
        mock_repository.get_inventory.return_value = mock_inventory
        mock_calculator.calculate_expiration_date.return_value = datetime(2024, 1, 27)
        
        # AI service fails
        mock_ai_service.enrich_ingredient_data.side_effect = Exception("AI service unavailable")
        
        # Act
        # Should not raise exception - AI enrichment is optional
        use_case_with_ai.execute("user_123", sample_ingredients_data)
        
        # Assert
        # Ingredients should still be added despite AI failure
        assert mock_repository.add_ingredient_stack.call_count == 2

    def test_add_ingredients_with_different_time_units(self, use_case, mock_repository, 
                                                     mock_calculator):
        """Test adding ingredients with different time units"""
        # Arrange
        mock_inventory = Mock()
        mock_repository.get_inventory.return_value = mock_inventory
        mock_calculator.calculate_expiration_date.return_value = datetime(2024, 1, 27)
        
        ingredients_with_different_units = [
            {
                "name": "Leche",
                "type_unit": "ml",
                "storage_type": "refrigerador",
                "tips": "Mantener frío",
                "image_path": "https://example.com/leche.jpg",
                "quantity": 1000,
                "expiration_time": 1,
                "time_unit": "weeks"
            },
            {
                "name": "Pan",
                "type_unit": "piezas",
                "storage_type": "despensa",
                "tips": "Lugar seco",
                "image_path": "https://example.com/pan.jpg",
                "quantity": 2,
                "expiration_time": 3,
                "time_unit": "days"
            }
        ]
        
        # Act
        use_case.execute("user_123", ingredients_with_different_units)
        
        # Assert
        assert mock_repository.add_ingredient_stack.call_count == 2
        assert mock_calculator.calculate_expiration_date.call_count == 2

    def test_add_ingredients_concurrent_processing(self, use_case_with_ai, mock_repository,
                                                  mock_calculator, mock_ai_service):
        """Test that concurrent processing works correctly with multiple ingredients"""
        # Arrange
        mock_inventory = Mock()
        mock_repository.get_inventory.return_value = mock_inventory
        mock_calculator.calculate_expiration_date.return_value = datetime(2024, 1, 27)
        
        # Large list of ingredients to test concurrent processing
        many_ingredients = []
        for i in range(10):
            many_ingredients.append({
                "name": f"Ingredient_{i}",
                "type_unit": "gr",
                "storage_type": "despensa",
                "tips": f"Tips for ingredient {i}",
                "image_path": f"https://example.com/ingredient_{i}.jpg",
                "quantity": 100 + i,
                "expiration_time": 1,
                "time_unit": "weeks"
            })
        
        # Act
        use_case_with_ai.execute("user_123", many_ingredients)
        
        # Assert
        assert mock_repository.add_ingredient_stack.call_count == 10

    def test_add_ingredients_preserves_original_data(self, use_case, mock_repository, 
                                                   mock_calculator, sample_ingredients_data):
        """Test that original ingredient data is preserved during processing"""
        # Arrange
        mock_inventory = Mock()
        mock_repository.get_inventory.return_value = mock_inventory
        mock_calculator.calculate_expiration_date.return_value = datetime(2024, 1, 27)
        
        original_data = sample_ingredients_data.copy()
        
        # Act
        use_case.execute("user_123", sample_ingredients_data)
        
        # Assert
        # Original data should not be modified
        assert sample_ingredients_data == original_data