"""
Unit tests for InventoryCalculator abstract interface
Tests the contract and behavior expectations for inventory calculation implementations
"""
import pytest
from abc import ABCMeta
from datetime import datetime, timedelta
from src.domain.services.inventory_calculator import InventoryCalculator
from src.domain.models.ingredient import Ingredient, IngredientStack
from src.domain.models.food_item import FoodItem


class TestInventoryCalculator:
    """Test suite for InventoryCalculator abstract interface"""
    
    def test_inventory_calculator_is_abstract(self):
        """Test that InventoryCalculator is an abstract base class"""
        # Act & Assert
        assert InventoryCalculator.__bases__ == (ABCMeta,)
        
        # Should not be able to instantiate directly
        with pytest.raises(TypeError):
            InventoryCalculator()
    
    def test_required_methods_exist(self):
        """Test that all required abstract methods are defined"""
        # Arrange
        expected_methods = [
            'calculate_expiration_date',
            'calculate_value', 
            'get_next_expiration',
            'total_quantity',
            'expired_items'
        ]
        
        # Act & Assert
        for method_name in expected_methods:
            assert hasattr(InventoryCalculator, method_name)
            method = getattr(InventoryCalculator, method_name)
            assert callable(method)


class ConcreteInventoryCalculator(InventoryCalculator):
    """Concrete implementation for testing purposes"""
    
    def calculate_expiration_date(self, added_at: datetime, time_value: int, time_unit: str) -> datetime:
        """Calculate expiration date based on time value and unit"""
        if time_unit.lower() in ['day', 'days']:
            return added_at + timedelta(days=time_value)
        elif time_unit.lower() in ['week', 'weeks']:
            return added_at + timedelta(weeks=time_value)
        elif time_unit.lower() in ['month', 'months']:
            return added_at + timedelta(days=time_value * 30)  # Approximate
        elif time_unit.lower() in ['year', 'years']:
            return added_at + timedelta(days=time_value * 365)  # Approximate
        else:
            return added_at + timedelta(days=time_value)  # Default to days
    
    def calculate_value(self, item) -> dict:
        """Calculate various values for an inventory item"""
        if isinstance(item, Ingredient):
            total_qty = self.total_quantity(item)
            next_exp = self.get_next_expiration(item)
            return {
                "total_quantity": total_qty,
                "next_expiration": next_exp,
                "stack_count": len(item.stacks),
                "type": "ingredient"
            }
        elif isinstance(item, FoodItem):
            return {
                "calories": item.calories,
                "expiration_date": item.expiration_date,
                "serving_quantity": item.serving_quantity,
                "type": "food_item"
            }
        else:
            return {"type": "unknown"}
    
    def get_next_expiration(self, ingredient: Ingredient) -> datetime:
        """Get the next expiration date from ingredient stacks"""
        if not ingredient.stacks:
            return None
        return min(stack.expiration_date for stack in ingredient.stacks)
    
    def total_quantity(self, ingredient: Ingredient) -> float:
        """Calculate total quantity across all stacks"""
        return sum(stack.quantity for stack in ingredient.stacks)
    
    def expired_items(self, inventory_items: list, as_of: datetime) -> list:
        """Find expired items as of a specific date"""
        expired = []
        for item in inventory_items:
            if isinstance(item, Ingredient):
                if item.stacks:
                    earliest_exp = min(stack.expiration_date for stack in item.stacks)
                    if earliest_exp <= as_of:
                        expired.append(item)
            elif isinstance(item, FoodItem):
                if item.expiration_date <= as_of:
                    expired.append(item)
        return expired


class TestConcreteInventoryCalculator:
    """Test suite for concrete InventoryCalculator implementation"""
    
    @pytest.fixture
    def calculator(self):
        """Concrete calculator for testing"""
        return ConcreteInventoryCalculator()
    
    @pytest.fixture
    def sample_ingredient(self):
        """Sample ingredient with multiple stacks"""
        ingredient = Ingredient(
            name="Tomate",
            type_unit="kg", 
            storage_type="Refrigerator",
            tips="Keep fresh",
            image_path="/images/tomate.jpg"
        )
        
        # Add stacks with different quantities and expiration dates
        now = datetime.now()
        ingredient.add_stack(IngredientStack(1.0, "kg", now + timedelta(days=3), now))
        ingredient.add_stack(IngredientStack(0.5, "kg", now + timedelta(days=7), now))
        ingredient.add_stack(IngredientStack(2.0, "kg", now + timedelta(days=1), now))  # Expires first
        
        return ingredient
    
    @pytest.fixture
    def sample_food_item(self):
        """Sample food item"""
        return FoodItem(
            name="Pizza",
            main_ingredients=["Masa", "Tomate", "Queso"],
            category="Comida Preparada",
            calories=250.0,
            description="Pizza casera",
            storage_type="Refrigerator",
            expiration_time=3,
            time_unit="days",
            tips="Calentar antes de consumir",
            serving_quantity=1,
            image_path="/images/pizza.jpg",
            added_at=datetime.now(),
            expiration_date=datetime.now() + timedelta(days=3)
        )
    
    def test_calculate_expiration_date_days(self, calculator):
        """Test expiration calculation with days"""
        # Arrange
        added_at = datetime(2024, 1, 1, 12, 0, 0)
        time_value = 5
        time_unit = "days"
        
        # Act
        result = calculator.calculate_expiration_date(added_at, time_value, time_unit)
        
        # Assert
        expected = datetime(2024, 1, 6, 12, 0, 0)
        assert result == expected
    
    @pytest.mark.parametrize("time_unit,expected_days", [
        ("days", 7),
        ("weeks", 49),  # 7 weeks = 49 days
        ("months", 210),  # 7 months ≈ 210 days
        ("years", 2555),  # 7 years ≈ 2555 days
        ("unknown", 7),  # Default to days
    ])
    def test_calculate_expiration_date_various_units(self, calculator, time_unit, expected_days):
        """Test expiration calculation with various time units"""
        # Arrange
        added_at = datetime(2024, 1, 1)
        time_value = 7
        
        # Act
        result = calculator.calculate_expiration_date(added_at, time_value, time_unit)
        
        # Assert
        expected = added_at + timedelta(days=expected_days)
        assert result == expected
    
    def test_calculate_value_ingredient(self, calculator, sample_ingredient):
        """Test value calculation for ingredient"""
        # Act
        result = calculator.calculate_value(sample_ingredient)
        
        # Assert
        assert result["type"] == "ingredient"
        assert result["total_quantity"] == 3.5  # 1.0 + 0.5 + 2.0
        assert result["stack_count"] == 3
        assert result["next_expiration"] is not None
        assert isinstance(result["next_expiration"], datetime)
    
    def test_calculate_value_food_item(self, calculator, sample_food_item):
        """Test value calculation for food item"""
        # Act
        result = calculator.calculate_value(sample_food_item)
        
        # Assert
        assert result["type"] == "food_item"
        assert result["calories"] == 250.0
        assert result["serving_quantity"] == 1
        assert result["expiration_date"] == sample_food_item.expiration_date
    
    def test_calculate_value_unknown_type(self, calculator):
        """Test value calculation for unknown item type"""
        # Arrange
        unknown_item = "not an ingredient or food item"
        
        # Act
        result = calculator.calculate_value(unknown_item)
        
        # Assert
        assert result["type"] == "unknown"
        assert len(result) == 1
    
    def test_get_next_expiration(self, calculator, sample_ingredient):
        """Test getting next expiration date from ingredient"""
        # Act
        result = calculator.get_next_expiration(sample_ingredient)
        
        # Assert
        assert result is not None
        assert isinstance(result, datetime)
        
        # Should be the earliest expiration (1 day from now)
        now = datetime.now()
        expected_earliest = now + timedelta(days=1)
        # Allow some tolerance for test execution time
        assert abs((result - expected_earliest).total_seconds()) < 60
    
    def test_get_next_expiration_empty_stacks(self, calculator):
        """Test getting next expiration from ingredient with no stacks"""
        # Arrange
        empty_ingredient = Ingredient(
            name="Empty",
            type_unit="kg",
            storage_type="Pantry", 
            tips="Empty ingredient",
            image_path="/path"
        )
        
        # Act
        result = calculator.get_next_expiration(empty_ingredient)
        
        # Assert
        assert result is None
    
    def test_total_quantity(self, calculator, sample_ingredient):
        """Test total quantity calculation"""
        # Act
        result = calculator.total_quantity(sample_ingredient)
        
        # Assert
        assert result == 3.5  # 1.0 + 0.5 + 2.0
    
    def test_total_quantity_empty_stacks(self, calculator):
        """Test total quantity with no stacks"""
        # Arrange
        empty_ingredient = Ingredient(
            name="Empty",
            type_unit="kg",
            storage_type="Pantry",
            tips="Empty ingredient", 
            image_path="/path"
        )
        
        # Act
        result = calculator.total_quantity(empty_ingredient)
        
        # Assert
        assert result == 0.0
    
    def test_expired_items_mixed_inventory(self, calculator, sample_ingredient, sample_food_item):
        """Test finding expired items in mixed inventory"""
        # Arrange
        now = datetime.now()
        
        # Create expired food item
        expired_food = FoodItem(
            name="Expired Food",
            main_ingredients=["Old stuff"],
            category="Expired",
            calories=100.0,
            description="This is expired",
            storage_type="Trash",
            expiration_time=1,
            time_unit="days",
            tips="Don't eat",
            serving_quantity=1,
            image_path="/images/expired.jpg",
            added_at=now - timedelta(days=5),
            expiration_date=now - timedelta(days=2)  # Expired 2 days ago
        )
        
        # Create fresh ingredient
        fresh_ingredient = Ingredient(
            name="Fresh",
            type_unit="kg",
            storage_type="Refrigerator",
            tips="Fresh ingredient",
            image_path="/path"
        )
        fresh_ingredient.add_stack(IngredientStack(
            1.0, "kg", now + timedelta(days=5), now
        ))
        
        inventory = [sample_ingredient, sample_food_item, expired_food, fresh_ingredient]
        
        # Act - check what's expired as of now
        result = calculator.expired_items(inventory, now)
        
        # Assert
        expired_names = [item.name for item in result]
        assert "Expired Food" in expired_names
        assert "Tomate" in expired_names  # Has stack expiring in 1 day, which is < now for test timing
        assert "Pizza" not in expired_names  # Fresh
        assert "Fresh" not in expired_names  # Fresh
    
    def test_expired_items_empty_inventory(self, calculator):
        """Test expired items with empty inventory"""
        # Act
        result = calculator.expired_items([], datetime.now())
        
        # Assert
        assert result == []
    
    def test_expired_items_no_expired(self, calculator, sample_food_item):
        """Test expired items when nothing is expired"""
        # Arrange
        future_date = datetime.now() - timedelta(days=10)  # Check from past
        
        # Act
        result = calculator.expired_items([sample_food_item], future_date)
        
        # Assert
        assert result == []