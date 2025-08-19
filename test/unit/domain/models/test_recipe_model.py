"""
Unit tests for Recipe domain model and related classes
Tests recipe creation, ingredient management, and business logic
"""
import pytest
from datetime import datetime
from src.domain.models.recipe import Recipe, RecipeIngredient, RecipeStep


class TestRecipeIngredient:
    """Test suite for RecipeIngredient class"""
    
    def test_recipe_ingredient_creation(self):
        """Test creating a recipe ingredient with all required fields"""
        # Arrange
        name = "Tomate"
        quantity = 2.5
        type_unit = "kg"
        
        # Act
        ingredient = RecipeIngredient(name=name, quantity=quantity, type_unit=type_unit)
        
        # Assert
        assert ingredient.name == name
        assert ingredient.quantity == quantity
        assert ingredient.type_unit == type_unit
    
    @pytest.mark.parametrize("name,quantity,type_unit", [
        ("Cebolla", 1.0, "unidad"),
        ("Aceite", 50.0, "ml"),
        ("Sal", 0.5, "cucharadita"),
        ("Pollo", 500.0, "g"),
    ])
    def test_recipe_ingredient_parametrized(self, name, quantity, type_unit):
        """Parametrized test for various ingredient scenarios"""
        # Act
        ingredient = RecipeIngredient(name=name, quantity=quantity, type_unit=type_unit)
        
        # Assert
        assert ingredient.name == name
        assert ingredient.quantity == quantity
        assert ingredient.type_unit == type_unit


class TestRecipeStep:
    """Test suite for RecipeStep class"""
    
    def test_recipe_step_creation(self):
        """Test creating a recipe step with order and description"""
        # Arrange
        step_order = 1
        description = "Precalentar el horno a 180°C"
        
        # Act
        step = RecipeStep(step_order=step_order, description=description)
        
        # Assert
        assert step.step_order == step_order
        assert step.description == description
    
    @pytest.mark.parametrize("order,description", [
        (1, "Primer paso de la receta"),
        (2, "Segundo paso con más detalle"),
        (10, "Último paso de decoración"),
    ])
    def test_recipe_step_parametrized(self, order, description):
        """Parametrized test for recipe steps"""
        # Act
        step = RecipeStep(step_order=order, description=description)
        
        # Assert
        assert step.step_order == order
        assert step.description == description


class TestRecipeModel:
    """Test suite for Recipe domain model"""
    
    @pytest.fixture
    def sample_ingredients(self):
        """Fixture providing sample recipe ingredients"""
        return [
            RecipeIngredient("Pollo", 500.0, "g"),
            RecipeIngredient("Cebolla", 1.0, "unidad"),
            RecipeIngredient("Ajo", 2.0, "dientes"),
        ]
    
    @pytest.fixture
    def sample_steps(self):
        """Fixture providing sample recipe steps"""
        return [
            RecipeStep(1, "Cortar el pollo en cubos"),
            RecipeStep(2, "Picar la cebolla y el ajo"),
            RecipeStep(3, "Cocinar todo junto por 20 minutos"),
        ]
    
    def test_recipe_creation_with_required_fields(self, sample_ingredients, sample_steps):
        """Test creating a recipe with all required fields"""
        # Arrange
        uid = "recipe-123"
        user_uid = "user-456"
        title = "Pollo con Vegetales"
        duration = "30 minutos"
        difficulty = "Fácil"
        footer = "¡Disfruta tu comida!"
        category = "Plato Principal"
        description = "Una deliciosa receta de pollo"
        
        # Act
        recipe = Recipe(
            uid=uid,
            user_uid=user_uid,
            title=title,
            duration=duration,
            difficulty=difficulty,
            ingredients=sample_ingredients,
            steps=sample_steps,
            footer=footer,
            category=category,
            description=description,
            image_path=None
        )
        
        # Assert
        assert recipe.uid == uid
        assert recipe.user_uid == user_uid
        assert recipe.title == title
        assert recipe.duration == duration
        assert recipe.difficulty == difficulty
        assert recipe.ingredients == sample_ingredients
        assert recipe.steps == sample_steps
        assert recipe.footer == footer
        assert recipe.category == category
        assert recipe.description == description
        assert recipe.generated_by_ai is True  # Default value
        assert recipe.image_status == "generating"  # Default value
        assert isinstance(recipe.saved_at, datetime)
        assert isinstance(recipe.generated_at, datetime)
    
    def test_recipe_creation_with_optional_fields(self, sample_ingredients, sample_steps):
        """Test creating a recipe with optional fields"""
        # Arrange
        saved_at = datetime(2023, 6, 15)
        generated_at = datetime(2023, 6, 14)
        image_path = "/images/recipe-123.jpg"
        
        # Act
        recipe = Recipe(
            uid="recipe-456",
            user_uid="user-789",
            title="Test Recipe",
            duration="45 minutes",
            difficulty="Medium",
            ingredients=sample_ingredients,
            steps=sample_steps,
            footer="Test footer",
            category="Test category",
            description="Test description",
            image_path=image_path,
            generated_by_ai=False,
            saved_at=saved_at,
            image_status="completed",
            generated_at=generated_at
        )
        
        # Assert
        assert recipe.image_path == image_path
        assert recipe.generated_by_ai is False
        assert recipe.saved_at == saved_at
        assert recipe.image_status == "completed"
        assert recipe.generated_at == generated_at
    
    def test_recipe_representation(self, sample_ingredients, sample_steps):
        """Test recipe string representation"""
        # Arrange
        uid = "recipe-repr"
        user_uid = "user-repr"
        title = "Repr Recipe"
        
        recipe = Recipe(
            uid=uid,
            user_uid=user_uid,
            title=title,
            duration="15 min",
            difficulty="Easy",
            ingredients=sample_ingredients,
            steps=sample_steps,
            footer="footer",
            category="category",
            description="description",
            image_path=None
        )
        
        # Act
        repr_str = repr(recipe)
        
        # Assert
        assert uid in repr_str
        assert user_uid in repr_str
        assert title in repr_str
        assert repr_str.startswith("Recipe(")
    
    def test_add_recipe_steps(self, sample_ingredients):
        """Test adding steps to a recipe"""
        # Arrange
        recipe = Recipe(
            uid="test",
            user_uid="user",
            title="Test",
            duration="10 min",
            difficulty="Easy",
            ingredients=sample_ingredients,
            steps=[],  # Start with empty steps
            footer="footer",
            category="category",
            description="description",
            image_path=None
        )
        
        new_steps = [
            RecipeStep(1, "New step 1"),
            RecipeStep(2, "New step 2"),
        ]
        
        # Act
        recipe.add_recipe_steps(new_steps)
        
        # Assert
        assert recipe.steps == new_steps
        assert len(recipe.steps) == 2
    
    def test_get_ingredients_names(self, sample_steps):
        """Test getting ingredient names from recipe"""
        # Arrange
        ingredients = [
            RecipeIngredient("Pasta", 200.0, "g"),
            RecipeIngredient("Queso", 100.0, "g"),
            RecipeIngredient("Tomate", 3.0, "unidades"),
        ]
        
        recipe = Recipe(
            uid="test",
            user_uid="user",
            title="Test",
            duration="20 min",
            difficulty="Easy",
            ingredients=ingredients,
            steps=sample_steps,
            footer="footer",
            category="category",
            description="description",
            image_path=None
        )
        
        # Act
        ingredient_names = recipe.get_ingredients_names()
        
        # Assert
        assert ingredient_names == ["Pasta", "Queso", "Tomate"]
        assert len(ingredient_names) == 3
    
    def test_add_recipe_ingredients(self, sample_steps):
        """Test adding ingredients to a recipe"""
        # Arrange
        recipe = Recipe(
            uid="test",
            user_uid="user",
            title="Test",
            duration="10 min",
            difficulty="Easy",
            ingredients=[],  # Start with empty ingredients
            steps=sample_steps,
            footer="footer",
            category="category",
            description="description",
            image_path=None
        )
        
        new_ingredients = [
            RecipeIngredient("New Ingredient 1", 100.0, "g"),
            RecipeIngredient("New Ingredient 2", 2.0, "cups"),
        ]
        
        # Act
        recipe.add_recipe_ingredients(new_ingredients)
        
        # Assert
        assert recipe.ingredients == new_ingredients
        assert len(recipe.ingredients) == 2
    
    def test_recipe_with_empty_ingredients_and_steps(self):
        """Test creating recipe with empty ingredients and steps lists"""
        # Act
        recipe = Recipe(
            uid="empty-recipe",
            user_uid="user-123",
            title="Empty Recipe",
            duration="0 min",
            difficulty="None",
            ingredients=[],
            steps=[],
            footer="No instructions",
            category="Incomplete",
            description="Recipe without content",
            image_path=None
        )
        
        # Assert
        assert len(recipe.ingredients) == 0
        assert len(recipe.steps) == 0
        assert recipe.get_ingredients_names() == []
    
    @pytest.mark.parametrize("difficulty,expected", [
        ("Fácil", "Fácil"),
        ("Medio", "Medio"),
        ("Difícil", "Difícil"),
        ("Expert", "Expert"),
    ])
    def test_recipe_difficulty_levels(self, difficulty, expected, sample_ingredients, sample_steps):
        """Parametrized test for different difficulty levels"""
        # Act
        recipe = Recipe(
            uid="test",
            user_uid="user",
            title="Test Recipe",
            duration="30 min",
            difficulty=difficulty,
            ingredients=sample_ingredients,
            steps=sample_steps,
            footer="footer",
            category="category",
            description="description",
            image_path=None
        )
        
        # Assert
        assert recipe.difficulty == expected
    
    def test_recipe_default_timestamps(self, sample_ingredients, sample_steps):
        """Test that recipes get default timestamps when not provided"""
        # Arrange
        before_creation = datetime.now()
        
        # Act
        recipe = Recipe(
            uid="timestamp-test",
            user_uid="user-123",
            title="Timestamp Recipe",
            duration="15 min",
            difficulty="Easy",
            ingredients=sample_ingredients,
            steps=sample_steps,
            footer="footer",
            category="category",
            description="description",
            image_path=None
        )
        
        after_creation = datetime.now()
        
        # Assert
        assert before_creation <= recipe.saved_at <= after_creation
        assert before_creation <= recipe.generated_at <= after_creation