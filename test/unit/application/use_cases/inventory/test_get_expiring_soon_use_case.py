"""
Unit tests for Get Expiring Soon Use Case
Tests retrieving items expiring soon functionality
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock

from src.application.use_cases.inventory.get_expiring_soon_use_case import GetExpiringSoonUseCase


class TestGetExpiringSoonUseCase:
    """Test suite for Get Expiring Soon Use Case"""

    @pytest.fixture
    def mock_repository(self):
        """Mock inventory repository"""
        return Mock()

    @pytest.fixture
    def use_case(self, mock_repository):
        """Create use case with mocked dependencies"""
        return GetExpiringSoonUseCase(repository=mock_repository)

    @pytest.fixture
    def expiring_ingredients(self):
        """Sample expiring ingredients"""
        today = datetime.now()
        return [
            Mock(
                name="Tomate",
                quantity=3,
                unit="piezas",
                expiration_date=today + timedelta(days=1),
                storage_type="refrigerador",
                days_until_expiration=1
            ),
            Mock(
                name="Leche",
                quantity=1000,
                unit="ml",
                expiration_date=today + timedelta(days=2),
                storage_type="refrigerador",
                days_until_expiration=2
            )
        ]

    @pytest.fixture
    def expiring_foods(self):
        """Sample expiring foods"""
        today = datetime.now()
        return [
            Mock(
                name="Pizza Casera",
                quantity=1,
                unit="porción",
                expiration_date=today + timedelta(days=1),
                storage_type="refrigerador",
                days_until_expiration=1
            )
        ]

    def test_get_expiring_soon_success(self, use_case, mock_repository, 
                                     expiring_ingredients, expiring_foods):
        """Test successful retrieval of expiring items"""
        # Arrange
        mock_repository.get_expiring_soon_ingredients.return_value = expiring_ingredients
        mock_repository.get_expiring_soon_foods.return_value = expiring_foods
        
        # Act
        result = use_case.execute(user_uid="user_123", days_ahead=3)
        
        # Assert
        assert result["user_uid"] == "user_123"
        assert result["days_ahead"] == 3
        assert len(result["ingredients"]) == 2
        assert len(result["foods"]) == 1
        assert result["total_items"] == 3
        assert result["urgency_levels"]["critical"] >= 0  # Items expiring in 1 day
        assert result["urgency_levels"]["warning"] >= 0   # Items expiring in 2-3 days
        
        mock_repository.get_expiring_soon_ingredients.assert_called_once_with("user_123", 3)
        mock_repository.get_expiring_soon_foods.assert_called_once_with("user_123", 3)

    def test_get_expiring_soon_default_days(self, use_case, mock_repository):
        """Test retrieval with default days ahead"""
        # Arrange
        mock_repository.get_expiring_soon_ingredients.return_value = []
        mock_repository.get_expiring_soon_foods.return_value = []
        
        # Act
        result = use_case.execute(user_uid="user_123")
        
        # Assert
        assert result["days_ahead"] == 7  # Default value
        mock_repository.get_expiring_soon_ingredients.assert_called_once_with("user_123", 7)
        mock_repository.get_expiring_soon_foods.assert_called_once_with("user_123", 7)

    def test_get_expiring_soon_no_items(self, use_case, mock_repository):
        """Test retrieval when no items are expiring soon"""
        # Arrange
        mock_repository.get_expiring_soon_ingredients.return_value = []
        mock_repository.get_expiring_soon_foods.return_value = []
        
        # Act
        result = use_case.execute(user_uid="user_123", days_ahead=5)
        
        # Assert
        assert result["ingredients"] == []
        assert result["foods"] == []
        assert result["total_items"] == 0
        assert result["message"] == "No items expiring soon"

    def test_get_expiring_soon_ingredients_only(self, use_case, mock_repository, expiring_ingredients):
        """Test retrieval with ingredients only"""
        # Arrange
        mock_repository.get_expiring_soon_ingredients.return_value = expiring_ingredients
        mock_repository.get_expiring_soon_foods.return_value = []
        
        # Act
        result = use_case.execute(user_uid="user_123", days_ahead=3)
        
        # Assert
        assert len(result["ingredients"]) == 2
        assert result["foods"] == []
        assert result["total_items"] == 2

    def test_get_expiring_soon_foods_only(self, use_case, mock_repository, expiring_foods):
        """Test retrieval with foods only"""
        # Arrange
        mock_repository.get_expiring_soon_ingredients.return_value = []
        mock_repository.get_expiring_soon_foods.return_value = expiring_foods
        
        # Act
        result = use_case.execute(user_uid="user_123", days_ahead=3)
        
        # Assert
        assert result["ingredients"] == []
        assert len(result["foods"]) == 1
        assert result["total_items"] == 1

    def test_get_expiring_soon_urgency_levels(self, use_case, mock_repository):
        """Test urgency level categorization"""
        # Arrange
        today = datetime.now()
        critical_items = [
            Mock(days_until_expiration=0),  # Expired
            Mock(days_until_expiration=1)   # Critical
        ]
        warning_items = [
            Mock(days_until_expiration=2),  # Warning
            Mock(days_until_expiration=3)   # Warning
        ]
        
        mock_repository.get_expiring_soon_ingredients.return_value = critical_items
        mock_repository.get_expiring_soon_foods.return_value = warning_items
        
        # Act
        result = use_case.execute(user_uid="user_123", days_ahead=5)
        
        # Assert
        assert result["urgency_levels"]["critical"] == 2  # 0-1 days
        assert result["urgency_levels"]["warning"] == 2   # 2-3 days
        assert result["urgency_levels"]["moderate"] == 0  # 4-5 days

    def test_get_expiring_soon_with_recipes_suggestions(self, use_case, mock_repository, 
                                                      expiring_ingredients):
        """Test retrieval with recipe suggestions"""
        # Arrange
        mock_repository.get_expiring_soon_ingredients.return_value = expiring_ingredients
        mock_repository.get_expiring_soon_foods.return_value = []
        
        # Act
        result = use_case.execute(user_uid="user_123", days_ahead=3, include_recipe_suggestions=True)
        
        # Assert
        assert "recipe_suggestions" in result
        # Should suggest recipes based on expiring ingredients

    def test_get_expiring_soon_invalid_user_uid(self, use_case):
        """Test retrieval with invalid user UID"""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.execute(user_uid="")
        
        assert "User UID cannot be empty" in str(exc_info.value)

    def test_get_expiring_soon_none_user_uid(self, use_case):
        """Test retrieval with None user UID"""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.execute(user_uid=None)
        
        assert "User UID cannot be None" in str(exc_info.value)

    def test_get_expiring_soon_invalid_days_ahead(self, use_case):
        """Test retrieval with invalid days ahead"""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.execute(user_uid="user_123", days_ahead=0)
        
        assert "Days ahead must be positive" in str(exc_info.value)

    def test_get_expiring_soon_negative_days_ahead(self, use_case):
        """Test retrieval with negative days ahead"""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.execute(user_uid="user_123", days_ahead=-1)
        
        assert "Days ahead must be positive" in str(exc_info.value)

    def test_get_expiring_soon_repository_ingredients_error(self, use_case, mock_repository):
        """Test handling of ingredients repository error"""
        # Arrange
        mock_repository.get_expiring_soon_ingredients.side_effect = Exception("Ingredients query failed")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            use_case.execute(user_uid="user_123")
        
        assert str(exc_info.value) == "Ingredients query failed"

    def test_get_expiring_soon_repository_foods_error(self, use_case, mock_repository, expiring_ingredients):
        """Test handling of foods repository error"""
        # Arrange
        mock_repository.get_expiring_soon_ingredients.return_value = expiring_ingredients
        mock_repository.get_expiring_soon_foods.side_effect = Exception("Foods query failed")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            use_case.execute(user_uid="user_123")
        
        assert str(exc_info.value) == "Foods query failed"

    def test_get_expiring_soon_large_days_ahead(self, use_case, mock_repository):
        """Test retrieval with large days ahead value"""
        # Arrange
        mock_repository.get_expiring_soon_ingredients.return_value = []
        mock_repository.get_expiring_soon_foods.return_value = []
        
        # Act
        result = use_case.execute(user_uid="user_123", days_ahead=30)
        
        # Assert
        assert result["days_ahead"] == 30
        mock_repository.get_expiring_soon_ingredients.assert_called_once_with("user_123", 30)

    def test_get_expiring_soon_sorting_by_expiration(self, use_case, mock_repository):
        """Test that items are sorted by expiration date"""
        # Arrange
        today = datetime.now()
        mixed_items = [
            Mock(
                name="Item3",
                expiration_date=today + timedelta(days=3),
                days_until_expiration=3
            ),
            Mock(
                name="Item1",
                expiration_date=today + timedelta(days=1),
                days_until_expiration=1
            ),
            Mock(
                name="Item2",
                expiration_date=today + timedelta(days=2),
                days_until_expiration=2
            )
        ]
        
        mock_repository.get_expiring_soon_ingredients.return_value = mixed_items
        mock_repository.get_expiring_soon_foods.return_value = []
        
        # Act
        result = use_case.execute(user_uid="user_123", days_ahead=5)
        
        # Assert
        # Verify items are returned in order by expiration date
        ingredients = result["ingredients"]
        assert ingredients[0].name == "Item1"  # Expires first
        assert ingredients[1].name == "Item2"  # Expires second
        assert ingredients[2].name == "Item3"  # Expires last