"""
Unit tests for Get Inventory Content Use Case
Tests retrieving complete inventory content functionality
"""
import pytest
from datetime import datetime
from unittest.mock import Mock

from src.application.use_cases.inventory.get_inventory_content_use_case import GetInventoryContentUseCase


class TestGetInventoryContentUseCase:
    """Test suite for Get Inventory Content Use Case"""

    @pytest.fixture
    def mock_repository(self):
        """Mock inventory repository"""
        return Mock()

    @pytest.fixture
    def use_case(self, mock_repository):
        """Create use case with mocked dependencies"""
        return GetInventoryContentUseCase(repository=mock_repository)

    @pytest.fixture
    def sample_inventory(self):
        """Sample inventory data"""
        inventory = Mock()
        inventory.user_uid = "user_123"
        inventory.created_at = datetime(2024, 1, 15)
        inventory.updated_at = datetime(2024, 1, 20)
        return inventory

    @pytest.fixture
    def sample_ingredients(self):
        """Sample ingredient stacks"""
        return [
            Mock(
                name="Tomate",
                quantity=5,
                unit="piezas",
                expiration_date=datetime(2024, 1, 25),
                storage_type="refrigerador"
            ),
            Mock(
                name="Cebolla",
                quantity=500,
                unit="gr",
                expiration_date=datetime(2024, 2, 1),
                storage_type="despensa"
            )
        ]

    @pytest.fixture
    def sample_foods(self):
        """Sample food items"""
        return [
            Mock(
                name="Pizza Casera",
                quantity=2,
                unit="porciones",
                expiration_date=datetime(2024, 1, 22),
                storage_type="refrigerador"
            )
        ]

    def test_get_inventory_content_success(self, use_case, mock_repository, sample_inventory, 
                                         sample_ingredients, sample_foods):
        """Test successful inventory content retrieval"""
        # Arrange
        mock_repository.get_inventory.return_value = sample_inventory
        mock_repository.get_all_ingredient_stacks.return_value = sample_ingredients
        mock_repository.get_all_food_items.return_value = sample_foods
        
        # Act
        result = use_case.execute(user_uid="user_123")
        
        # Assert
        assert result["user_uid"] == "user_123"
        assert "created_at" in result
        assert "updated_at" in result
        assert len(result["ingredients"]) == 2
        assert len(result["foods"]) == 1
        assert result["total_items"] == 3
        
        mock_repository.get_inventory.assert_called_once_with("user_123")
        mock_repository.get_all_ingredient_stacks.assert_called_once_with("user_123")
        mock_repository.get_all_food_items.assert_called_once_with("user_123")

    def test_get_inventory_content_no_inventory(self, use_case, mock_repository):
        """Test getting content when no inventory exists"""
        # Arrange
        mock_repository.get_inventory.return_value = None
        
        # Act
        result = use_case.execute(user_uid="user_123")
        
        # Assert
        assert result["user_uid"] == "user_123"
        assert result["ingredients"] == []
        assert result["foods"] == []
        assert result["total_items"] == 0
        assert result["message"] == "No inventory found for user"
        
        mock_repository.get_inventory.assert_called_once_with("user_123")
        mock_repository.get_all_ingredient_stacks.assert_not_called()
        mock_repository.get_all_food_items.assert_not_called()

    def test_get_inventory_content_empty_inventory(self, use_case, mock_repository, sample_inventory):
        """Test getting content of empty inventory"""
        # Arrange
        mock_repository.get_inventory.return_value = sample_inventory
        mock_repository.get_all_ingredient_stacks.return_value = []
        mock_repository.get_all_food_items.return_value = []
        
        # Act
        result = use_case.execute(user_uid="user_123")
        
        # Assert
        assert result["user_uid"] == "user_123"
        assert result["ingredients"] == []
        assert result["foods"] == []
        assert result["total_items"] == 0

    def test_get_inventory_content_ingredients_only(self, use_case, mock_repository, 
                                                  sample_inventory, sample_ingredients):
        """Test getting content with ingredients only"""
        # Arrange
        mock_repository.get_inventory.return_value = sample_inventory
        mock_repository.get_all_ingredient_stacks.return_value = sample_ingredients
        mock_repository.get_all_food_items.return_value = []
        
        # Act
        result = use_case.execute(user_uid="user_123")
        
        # Assert
        assert len(result["ingredients"]) == 2
        assert result["foods"] == []
        assert result["total_items"] == 2

    def test_get_inventory_content_foods_only(self, use_case, mock_repository, 
                                            sample_inventory, sample_foods):
        """Test getting content with foods only"""
        # Arrange
        mock_repository.get_inventory.return_value = sample_inventory
        mock_repository.get_all_ingredient_stacks.return_value = []
        mock_repository.get_all_food_items.return_value = sample_foods
        
        # Act
        result = use_case.execute(user_uid="user_123")
        
        # Assert
        assert result["ingredients"] == []
        assert len(result["foods"]) == 1
        assert result["total_items"] == 1

    def test_get_inventory_content_with_categorization(self, use_case, mock_repository, 
                                                     sample_inventory, sample_ingredients):
        """Test getting content with storage type categorization"""
        # Arrange
        mock_repository.get_inventory.return_value = sample_inventory
        mock_repository.get_all_ingredient_stacks.return_value = sample_ingredients
        mock_repository.get_all_food_items.return_value = []
        
        # Act
        result = use_case.execute(user_uid="user_123", categorize_by_storage=True)
        
        # Assert
        assert "storage_categories" in result
        assert "refrigerador" in result["storage_categories"]
        assert "despensa" in result["storage_categories"]
        assert len(result["storage_categories"]["refrigerador"]) == 1
        assert len(result["storage_categories"]["despensa"]) == 1

    def test_get_inventory_content_with_expiration_analysis(self, use_case, mock_repository, 
                                                          sample_inventory, sample_ingredients):
        """Test getting content with expiration analysis"""
        # Arrange
        mock_repository.get_inventory.return_value = sample_inventory
        mock_repository.get_all_ingredient_stacks.return_value = sample_ingredients
        mock_repository.get_all_food_items.return_value = []
        
        # Act
        result = use_case.execute(user_uid="user_123", include_expiration_analysis=True)
        
        # Assert
        assert "expiration_analysis" in result
        assert "expiring_soon" in result["expiration_analysis"]
        assert "expired" in result["expiration_analysis"]
        assert "fresh" in result["expiration_analysis"]

    def test_get_inventory_content_invalid_user_uid(self, use_case):
        """Test getting content with invalid user UID"""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.execute(user_uid="")
        
        assert "User UID cannot be empty" in str(exc_info.value)

    def test_get_inventory_content_none_user_uid(self, use_case):
        """Test getting content with None user UID"""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.execute(user_uid=None)
        
        assert "User UID cannot be None" in str(exc_info.value)

    def test_get_inventory_content_repository_error_propagation(self, use_case, mock_repository):
        """Test that repository errors are propagated"""
        # Arrange
        mock_repository.get_inventory.side_effect = Exception("Database connection error")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            use_case.execute(user_uid="user_123")
        
        assert str(exc_info.value) == "Database connection error"

    def test_get_inventory_content_ingredients_error_handling(self, use_case, mock_repository, sample_inventory):
        """Test handling of ingredient retrieval errors"""
        # Arrange
        mock_repository.get_inventory.return_value = sample_inventory
        mock_repository.get_all_ingredient_stacks.side_effect = Exception("Ingredient retrieval failed")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            use_case.execute(user_uid="user_123")
        
        assert str(exc_info.value) == "Ingredient retrieval failed"

    def test_get_inventory_content_foods_error_handling(self, use_case, mock_repository, 
                                                      sample_inventory, sample_ingredients):
        """Test handling of food items retrieval errors"""
        # Arrange
        mock_repository.get_inventory.return_value = sample_inventory
        mock_repository.get_all_ingredient_stacks.return_value = sample_ingredients
        mock_repository.get_all_food_items.side_effect = Exception("Food retrieval failed")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            use_case.execute(user_uid="user_123")
        
        assert str(exc_info.value) == "Food retrieval failed"