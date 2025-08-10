"""
Unit tests for Inventory domain model and related classes
Tests inventory management, ingredient stacks, and food items
"""
import pytest
from datetime import datetime, timedelta
from src.domain.models.inventory import Inventory
from src.domain.models.ingredient import Ingredient, IngredientStack
from src.domain.models.food_item import FoodItem


class TestIngredientStack:
    """Test suite for IngredientStack class"""
    
    def test_ingredient_stack_creation(self):
        """Test creating an ingredient stack with all required fields"""
        # Arrange
        quantity = 500.0
        type_unit = "g"
        expiration_date = datetime(2024, 12, 31)
        added_at = datetime(2024, 1, 1)
        
        # Act
        stack = IngredientStack(
            quantity=quantity,
            type_unit=type_unit,
            expiration_date=expiration_date,
            added_at=added_at
        )
        
        # Assert
        assert stack.quantity == quantity
        assert stack.type_unit == type_unit
        assert stack.expiration_date == expiration_date
        assert stack.added_at == added_at
    
    def test_ingredient_stack_representation(self):
        """Test ingredient stack string representation"""
        # Arrange
        stack = IngredientStack(
            quantity=250.0,
            type_unit="ml",
            expiration_date=datetime(2024, 6, 15),
            added_at=datetime(2024, 1, 10)
        )
        
        # Act
        repr_str = repr(stack)
        
        # Assert
        assert "250.0" in repr_str
        assert "ml" in repr_str
        assert "2024-01-10" in repr_str
        assert "2024-06-15" in repr_str
        assert "IngredientStack" in repr_str


class TestIngredient:
    """Test suite for Ingredient class"""
    
    @pytest.fixture
    def sample_stacks(self):
        """Fixture providing sample ingredient stacks"""
        return [
            IngredientStack(200.0, "g", datetime(2024, 12, 31), datetime.now()),
            IngredientStack(300.0, "g", datetime(2024, 11, 30), datetime.now()),
            IngredientStack(150.0, "g", datetime(2025, 1, 15), datetime.now()),
        ]
    
    def test_ingredient_creation(self):
        """Test creating an ingredient with all required fields"""
        # Arrange
        name = "Tomate"
        type_unit = "kg"
        storage_type = "Refrigerator"
        tips = "Mantener fresco en refrigerador"
        image_path = "/images/tomate.jpg"
        
        # Act
        ingredient = Ingredient(
            name=name,
            type_unit=type_unit,
            storage_type=storage_type,
            tips=tips,
            image_path=image_path
        )
        
        # Assert
        assert ingredient.name == name
        assert ingredient.type_unit == type_unit
        assert ingredient.storage_type == storage_type
        assert ingredient.tips == tips
        assert ingredient.image_path == image_path
        assert ingredient.stacks == []  # Initially empty
    
    def test_add_stack_to_ingredient(self):
        """Test adding stacks to an ingredient"""
        # Arrange
        ingredient = Ingredient("Arroz", "kg", "Pantry", "Lugar seco", "/images/arroz.jpg")
        stack = IngredientStack(1.0, "kg", datetime(2025, 12, 31), datetime.now())
        
        # Act
        ingredient.add_stack(stack)
        
        # Assert
        assert len(ingredient.stacks) == 1
        assert ingredient.stacks[0] == stack
    
    def test_get_total_quantity_with_multiple_stacks(self, sample_stacks):
        """Test calculating total quantity from multiple stacks"""
        # Arrange
        ingredient = Ingredient("Harina", "kg", "Pantry", "Lugar seco", "/images/harina.jpg")
        for stack in sample_stacks:
            ingredient.add_stack(stack)
        
        # Act
        total_quantity = ingredient.get_total_quantity()
        
        # Assert
        expected_total = 200.0 + 300.0 + 150.0  # Sum of sample stacks
        assert total_quantity == expected_total
    
    def test_get_total_quantity_with_no_stacks(self):
        """Test total quantity calculation with empty stacks"""
        # Arrange
        ingredient = Ingredient("Empty", "g", "Pantry", "Tips", "/path")
        
        # Act
        total_quantity = ingredient.get_total_quantity()
        
        # Assert
        assert total_quantity == 0.0
    
    def test_get_nearest_expiration_with_multiple_stacks(self):
        """Test finding nearest expiration date from multiple stacks"""
        # Arrange
        ingredient = Ingredient("Leche", "l", "Refrigerator", "Mantener fría", "/images/leche.jpg")
        
        # Add stacks with different expiration dates
        far_future = IngredientStack(1.0, "l", datetime(2025, 12, 31), datetime.now())
        near_future = IngredientStack(1.0, "l", datetime(2024, 6, 15), datetime.now())
        mid_future = IngredientStack(1.0, "l", datetime(2024, 12, 1), datetime.now())
        
        ingredient.add_stack(far_future)
        ingredient.add_stack(near_future)
        ingredient.add_stack(mid_future)
        
        # Act
        nearest_expiration = ingredient.get_nearest_expiration()
        
        # Assert
        assert nearest_expiration == datetime(2024, 6, 15)
    
    def test_get_nearest_expiration_with_no_stacks(self):
        """Test nearest expiration date with empty stacks"""
        # Arrange
        ingredient = Ingredient("Empty", "g", "Pantry", "Tips", "/path")
        
        # Act
        nearest_expiration = ingredient.get_nearest_expiration()
        
        # Assert
        assert nearest_expiration is None
    
    def test_ingredient_representation(self, sample_stacks):
        """Test ingredient string representation"""
        # Arrange
        ingredient = Ingredient("Cebolla", "kg", "Pantry", "Lugar seco", "/images/cebolla.jpg")
        ingredient.stacks = sample_stacks
        
        # Act
        repr_str = repr(ingredient)
        
        # Assert
        assert "Cebolla" in repr_str
        assert "Ingredient" in repr_str
        assert "stacks=" in repr_str


class TestFoodItem:
    """Test suite for FoodItem class"""
    
    def test_food_item_creation_with_all_fields(self):
        """Test creating a food item with all required fields"""
        # Arrange
        name = "Pizza Margherita"
        main_ingredients = ["Masa", "Tomate", "Mozzarella", "Albahaca"]
        category = "Comida Preparada"
        calories = 250.5
        description = "Pizza clásica italiana"
        storage_type = "Refrigerator"
        expiration_time = 3
        time_unit = "days"
        tips = "Calentar antes de consumir"
        serving_quantity = 1
        image_path = "/images/pizza.jpg"
        added_at = datetime(2024, 1, 1, 12, 0, 0)
        expiration_date = datetime(2024, 1, 4, 12, 0, 0)
        
        # Act
        food_item = FoodItem(
            name=name,
            main_ingredients=main_ingredients,
            category=category,
            calories=calories,
            description=description,
            storage_type=storage_type,
            expiration_time=expiration_time,
            time_unit=time_unit,
            tips=tips,
            serving_quantity=serving_quantity,
            image_path=image_path,
            added_at=added_at,
            expiration_date=expiration_date
        )
        
        # Assert
        assert food_item.name == name
        assert food_item.main_ingredients == main_ingredients
        assert food_item.category == category
        assert food_item.calories == calories
        assert food_item.description == description
        assert food_item.storage_type == storage_type
        assert food_item.expiration_time == expiration_time
        assert food_item.time_unit == time_unit
        assert food_item.tips == tips
        assert food_item.serving_quantity == serving_quantity
        assert food_item.image_path == image_path
        assert food_item.added_at == added_at
        assert food_item.expiration_date == expiration_date
    
    def test_food_item_with_optional_calories_none(self):
        """Test creating food item with None calories"""
        # Act
        food_item = FoodItem(
            name="Unknown Food",
            main_ingredients=["Unknown"],
            category="Unknown",
            calories=None,
            description="Food with unknown calories",
            storage_type="Pantry",
            expiration_time=1,
            time_unit="week",
            tips="Handle with care",
            serving_quantity=1,
            image_path="/images/unknown.jpg",
            added_at=datetime.now(),
            expiration_date=datetime.now() + timedelta(weeks=1)
        )
        
        # Assert
        assert food_item.calories is None
    
    def test_food_item_representation(self):
        """Test food item string representation"""
        # Arrange
        added_at = datetime(2024, 2, 15)
        food_item = FoodItem(
            name="Lasagna",
            main_ingredients=["Pasta", "Meat", "Cheese"],
            category="Main Dish",
            calories=400.0,
            description="Homemade lasagna",
            storage_type="Freezer",
            expiration_time=30,
            time_unit="days",
            tips="Defrost before heating",
            serving_quantity=2,
            image_path="/images/lasagna.jpg",
            added_at=added_at,
            expiration_date=added_at + timedelta(days=30)
        )
        
        # Act
        repr_str = repr(food_item)
        
        # Assert
        assert "Lasagna" in repr_str
        assert "2024-02-15" in repr_str
        assert "FoodItem" in repr_str


class TestInventory:
    """Test suite for Inventory class"""
    
    @pytest.fixture
    def sample_inventory(self):
        """Fixture providing a sample inventory"""
        return Inventory(user_uid="user-123")
    
    @pytest.fixture
    def sample_food_item(self):
        """Fixture providing a sample food item"""
        return FoodItem(
            name="Sandwich",
            main_ingredients=["Bread", "Ham", "Cheese"],
            category="Quick Meal",
            calories=350.0,
            description="Simple sandwich",
            storage_type="Refrigerator",
            expiration_time=2,
            time_unit="days",
            tips="Consume quickly",
            serving_quantity=1,
            image_path="/images/sandwich.jpg",
            added_at=datetime.now(),
            expiration_date=datetime.now() + timedelta(days=2)
        )
    
    def test_inventory_creation(self):
        """Test creating an empty inventory"""
        # Arrange
        user_uid = "test-user-456"
        
        # Act
        inventory = Inventory(user_uid=user_uid)
        
        # Assert
        assert inventory.user_uid == user_uid
        assert inventory.ingredients == {}
        assert inventory.foods == []
    
    def test_add_ingredient_stack_new_ingredient(self, sample_inventory):
        """Test adding an ingredient stack for a new ingredient"""
        # Arrange
        name = "Tomate"
        stack = IngredientStack(500.0, "g", datetime(2024, 12, 31), datetime.now())
        type_unit = "g"
        storage_type = "Refrigerator"
        tips = "Keep fresh"
        image_path = "/images/tomate.jpg"
        
        # Act
        sample_inventory.add_ingredient_stack(
            name=name,
            stack=stack,
            type_unit=type_unit,
            storage_type=storage_type,
            tips=tips,
            image_path=image_path
        )
        
        # Assert
        assert name in sample_inventory.ingredients
        ingredient = sample_inventory.ingredients[name]
        assert ingredient.name == name
        assert ingredient.type_unit == type_unit
        assert ingredient.storage_type == storage_type
        assert ingredient.tips == tips
        assert ingredient.image_path == image_path
        assert len(ingredient.stacks) == 1
        assert ingredient.stacks[0] == stack
    
    def test_add_ingredient_stack_existing_ingredient(self, sample_inventory):
        """Test adding a stack to an existing ingredient"""
        # Arrange
        name = "Cebolla"
        first_stack = IngredientStack(300.0, "g", datetime(2024, 11, 30), datetime.now())
        second_stack = IngredientStack(200.0, "g", datetime(2024, 12, 15), datetime.now())
        
        # Add first stack (creates ingredient)
        sample_inventory.add_ingredient_stack(
            name=name,
            stack=first_stack,
            type_unit="g",
            storage_type="Pantry",
            tips="Store in dry place",
            image_path="/images/cebolla.jpg"
        )
        
        # Act - Add second stack to existing ingredient
        sample_inventory.add_ingredient_stack(
            name=name,
            stack=second_stack,
            type_unit="g",
            storage_type="Pantry",
            tips="Store in dry place",
            image_path="/images/cebolla.jpg"
        )
        
        # Assert
        assert name in sample_inventory.ingredients
        ingredient = sample_inventory.ingredients[name]
        assert len(ingredient.stacks) == 2
        assert first_stack in ingredient.stacks
        assert second_stack in ingredient.stacks
        assert ingredient.get_total_quantity() == 500.0  # 300 + 200
    
    def test_add_food_item(self, sample_inventory, sample_food_item):
        """Test adding a food item to inventory"""
        # Act
        sample_inventory.add_food_item(sample_food_item)
        
        # Assert
        assert len(sample_inventory.foods) == 1
        assert sample_inventory.foods[0] == sample_food_item
    
    def test_get_ingredient_existing(self, sample_inventory):
        """Test getting an existing ingredient from inventory"""
        # Arrange
        name = "Arroz"
        stack = IngredientStack(1000.0, "g", datetime(2025, 6, 30), datetime.now())
        sample_inventory.add_ingredient_stack(
            name=name,
            stack=stack,
            type_unit="g",
            storage_type="Pantry",
            tips="Keep dry",
            image_path="/images/arroz.jpg"
        )
        
        # Act
        ingredient = sample_inventory.get_ingredient(name)
        
        # Assert
        assert ingredient is not None
        assert ingredient.name == name
        assert len(ingredient.stacks) == 1
    
    def test_get_ingredient_non_existing(self, sample_inventory):
        """Test getting a non-existing ingredient from inventory"""
        # Act
        ingredient = sample_inventory.get_ingredient("NonExistent")
        
        # Assert
        assert ingredient is None
    
    def test_get_expiring_soon_within_default_days(self, sample_inventory):
        """Test getting ingredients expiring within default 3 days"""
        # Arrange
        today = datetime.now()
        tomorrow = today + timedelta(days=1)
        next_week = today + timedelta(days=7)
        
        # Add ingredient expiring soon
        expiring_stack = IngredientStack(200.0, "g", tomorrow, today)
        sample_inventory.add_ingredient_stack(
            name="ExpiringSoon",
            stack=expiring_stack,
            type_unit="g",
            storage_type="Refrigerator",
            tips="Use quickly",
            image_path="/images/expiring.jpg"
        )
        
        # Add ingredient not expiring soon
        not_expiring_stack = IngredientStack(500.0, "g", next_week, today)
        sample_inventory.add_ingredient_stack(
            name="NotExpiring",
            stack=not_expiring_stack,
            type_unit="g",
            storage_type="Pantry",
            tips="Keep dry",
            image_path="/images/not_expiring.jpg"
        )
        
        # Act
        expiring_ingredients = sample_inventory.get_expiring_soon()
        
        # Assert
        assert len(expiring_ingredients) == 1
        assert "ExpiringSoon" in expiring_ingredients
        assert "NotExpiring" not in expiring_ingredients
    
    def test_get_expiring_soon_custom_days(self, sample_inventory):
        """Test getting ingredients expiring within custom number of days"""
        # Arrange
        today = datetime.now()
        in_5_days = today + timedelta(days=5)
        in_10_days = today + timedelta(days=10)
        
        # Add ingredient expiring in 5 days
        stack_5_days = IngredientStack(300.0, "g", in_5_days, today)
        sample_inventory.add_ingredient_stack(
            name="Expires5Days",
            stack=stack_5_days,
            type_unit="g",
            storage_type="Refrigerator",
            tips="Use soon",
            image_path="/images/expires5.jpg"
        )
        
        # Add ingredient expiring in 10 days
        stack_10_days = IngredientStack(400.0, "g", in_10_days, today)
        sample_inventory.add_ingredient_stack(
            name="Expires10Days",
            stack=stack_10_days,
            type_unit="g",
            storage_type="Pantry",
            tips="Store well",
            image_path="/images/expires10.jpg"
        )
        
        # Act
        expiring_within_7_days = sample_inventory.get_expiring_soon(within_days=7)
        
        # Assert
        assert len(expiring_within_7_days) == 1
        assert "Expires5Days" in expiring_within_7_days
        assert "Expires10Days" not in expiring_within_7_days
    
    def test_get_expiring_soon_no_ingredients(self, sample_inventory):
        """Test getting expiring ingredients from empty inventory"""
        # Act
        expiring_ingredients = sample_inventory.get_expiring_soon()
        
        # Assert
        assert len(expiring_ingredients) == 0
        assert expiring_ingredients == []
    
    def test_inventory_representation(self, sample_inventory, sample_food_item):
        """Test inventory string representation"""
        # Arrange
        stack = IngredientStack(100.0, "g", datetime(2024, 12, 31), datetime.now())
        sample_inventory.add_ingredient_stack(
            name="TestIngredient",
            stack=stack,
            type_unit="g",
            storage_type="Pantry",
            tips="Test tips",
            image_path="/images/test.jpg"
        )
        sample_inventory.add_food_item(sample_food_item)
        
        # Act
        repr_str = repr(sample_inventory)
        
        # Assert
        assert "user-123" in repr_str
        assert "TestIngredient" in repr_str
        assert "foods=1" in repr_str
        assert "Inventory" in repr_str