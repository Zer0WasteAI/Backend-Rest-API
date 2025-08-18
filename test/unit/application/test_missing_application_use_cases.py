"""
Unit tests for Application Use Cases
Tests business logic use cases in the application layer
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, date


class TestApplicationUseCases:
    """Test suite for Application Use Cases"""

    # Recipe Use Cases Tests
    def test_generate_custom_recipe_use_case_success(self):
        """Test generate custom recipe use case successful execution"""
        # Arrange
        from src.application.use_cases.recipes.generate_custom_recipe_use_case import GenerateCustomRecipeUseCase
        
        mock_recipe_service = Mock()
        mock_recipe_service.generate_custom_recipe.return_value = {
            "id": 1,
            "title": "Custom Tomato Soup",
            "ingredients": ["Tomato", "Onion"],
            "instructions": ["Cook tomatoes", "Add onions"]
        }
        
        use_case = GenerateCustomRecipeUseCase(recipe_service=mock_recipe_service)
        
        recipe_request = {
            "available_ingredients": ["Tomato", "Onion", "Garlic"],
            "cuisine_preference": "italian",
            "dietary_restrictions": [],
            "user_id": "user_123"
        }
        
        # Act
        result = use_case.execute(recipe_request)
        
        # Assert
        assert result["id"] == 1
        assert result["title"] == "Custom Tomato Soup"
        mock_recipe_service.generate_custom_recipe.assert_called_once()

    def test_save_recipe_use_case_success(self):
        """Test save recipe use case successful execution"""
        # Arrange
        from src.application.use_cases.recipes.save_recipe_use_case import SaveRecipeUseCase
        
        mock_recipe_repo = Mock()
        mock_recipe_repo.save_recipe.return_value = {
            "id": 1,
            "title": "Saved Recipe",
            "status": "saved",
            "user_id": "user_123"
        }
        
        use_case = SaveRecipeUseCase(recipe_repository=mock_recipe_repo)
        
        recipe_data = {
            "title": "Saved Recipe",
            "ingredients": ["Ingredient1", "Ingredient2"],
            "user_id": "user_123"
        }
        
        # Act
        result = use_case.execute(recipe_data)
        
        # Assert
        assert result["id"] == 1
        assert result["status"] == "saved"
        mock_recipe_repo.save_recipe.assert_called_once()

    def test_add_recipe_to_favorites_use_case_success(self):
        """Test add recipe to favorites use case successful execution"""
        # Arrange
        from src.application.use_cases.recipes.add_recipe_to_favorites_use_case import AddRecipeToFavoritesUseCase
        
        mock_favorites_repo = Mock()
        mock_favorites_repo.add_to_favorites.return_value = {
            "user_id": "user_123",
            "recipe_id": 1,
            "added_at": datetime.now().isoformat()
        }
        
        use_case = AddRecipeToFavoritesUseCase(favorites_repository=mock_favorites_repo)
        
        # Act
        result = use_case.execute(user_id="user_123", recipe_id=1)
        
        # Assert
        assert result["user_id"] == "user_123"
        assert result["recipe_id"] == 1
        mock_favorites_repo.add_to_favorites.assert_called_once()

    def test_get_favorite_recipes_use_case_success(self):
        """Test get favorite recipes use case successful execution"""
        # Arrange
        from src.application.use_cases.recipes.get_favorite_recipes_use_case import GetFavoriteRecipesUseCase
        
        mock_favorites_repo = Mock()
        mock_favorites_repo.get_user_favorites.return_value = [
            {"id": 1, "title": "Pasta Carbonara", "added_at": "2024-01-01"},
            {"id": 2, "title": "Chicken Curry", "added_at": "2024-01-02"}
        ]
        
        use_case = GetFavoriteRecipesUseCase(favorites_repository=mock_favorites_repo)
        
        # Act
        result = use_case.execute(user_id="user_123")
        
        # Assert
        assert len(result) == 2
        assert result[0]["title"] == "Pasta Carbonara"
        mock_favorites_repo.get_user_favorites.assert_called_once_with("user_123")

    # Inventory Use Cases Tests
    def test_add_item_to_inventory_use_case_success(self):
        """Test add item to inventory use case successful execution"""
        # Arrange
        from src.application.use_cases.inventory.add_item_to_inventory_use_case import AddItemToInventoryUseCase
        
        mock_inventory_repo = Mock()
        mock_inventory_repo.add_item.return_value = {
            "id": 1,
            "name": "Tomato",
            "quantity": 3,
            "expiry_date": "2024-01-20",
            "user_id": "user_123"
        }
        
        use_case = AddItemToInventoryUseCase(inventory_repository=mock_inventory_repo)
        
        item_data = {
            "name": "Tomato",
            "quantity": 3,
            "expiry_date": "2024-01-20",
            "user_id": "user_123"
        }
        
        # Act
        result = use_case.execute(item_data)
        
        # Assert
        assert result["id"] == 1
        assert result["name"] == "Tomato"
        mock_inventory_repo.add_item.assert_called_once()

    def test_get_foods_list_use_case_success(self):
        """Test get foods list use case successful execution"""
        # Arrange
        from src.application.use_cases.inventory.get_foods_list_use_case import GetFoodsListUseCase
        
        mock_inventory_repo = Mock()
        mock_inventory_repo.get_foods_by_user.return_value = [
            {"id": 1, "name": "Apple", "category": "fruits", "quantity": 5},
            {"id": 2, "name": "Bread", "category": "grains", "quantity": 1}
        ]
        
        use_case = GetFoodsListUseCase(inventory_repository=mock_inventory_repo)
        
        # Act
        result = use_case.execute(user_id="user_123")
        
        # Assert
        assert len(result) == 2
        assert result[0]["name"] == "Apple"
        mock_inventory_repo.get_foods_by_user.assert_called_once_with("user_123")

    def test_get_expiring_soon_use_case_success(self):
        """Test get expiring soon use case successful execution"""
        # Arrange
        from src.application.use_cases.inventory.get_expiring_soon_use_case import GetExpiringSoonUseCase
        
        mock_inventory_repo = Mock()
        mock_inventory_repo.get_expiring_items.return_value = [
            {"id": 1, "name": "Milk", "expiry_date": "2024-01-15", "days_until_expiry": 2},
            {"id": 2, "name": "Bread", "expiry_date": "2024-01-16", "days_until_expiry": 3}
        ]
        
        use_case = GetExpiringSoonUseCase(inventory_repository=mock_inventory_repo)
        
        # Act
        result = use_case.execute(user_id="user_123", days_ahead=7)
        
        # Assert
        assert len(result) == 2
        assert result[0]["days_until_expiry"] == 2
        mock_inventory_repo.get_expiring_items.assert_called_once()

    def test_mark_food_item_consumed_use_case_success(self):
        """Test mark food item consumed use case successful execution"""
        # Arrange
        from src.application.use_cases.inventory.mark_food_item_consumed_use_case import MarkFoodItemConsumedUseCase
        
        mock_inventory_repo = Mock()
        mock_inventory_repo.mark_consumed.return_value = {
            "id": 1,
            "name": "Apple",
            "status": "consumed",
            "consumed_at": datetime.now().isoformat()
        }
        
        use_case = MarkFoodItemConsumedUseCase(inventory_repository=mock_inventory_repo)
        
        # Act
        result = use_case.execute(food_id=1, user_id="user_123", quantity_consumed=2)
        
        # Assert
        assert result["status"] == "consumed"
        mock_inventory_repo.mark_consumed.assert_called_once()

    # Cooking Session Use Cases Tests
    def test_cooking_session_creation_success(self):
        """Test cooking session creation successful execution"""
        # Arrange
        from src.application.use_cases.cooking_session.start_cooking_session_use_case import StartCookingSessionUseCase
        
        mock_session_repo = Mock()
        mock_session_repo.create_session.return_value = {
            "id": 1,
            "recipe_id": 1,
            "status": "started",
            "started_at": datetime.now().isoformat(),
            "user_id": "user_123"
        }
        
        use_case = StartCookingSessionUseCase(session_repository=mock_session_repo)
        
        # Act
        result = use_case.execute(recipe_id=1, user_id="user_123")
        
        # Assert
        assert result["recipe_id"] == 1
        assert result["status"] == "started"
        mock_session_repo.create_session.assert_called_once()

    # Recognition Use Cases Tests
    def test_recognition_use_case_batch_processing(self):
        """Test recognition use case batch processing successful execution"""
        # Arrange
        from src.application.use_cases.recognition.recognize_batch_use_case import RecognizeBatchUseCase
        
        mock_ai_service = Mock()
        mock_ai_service.recognize_batch.return_value = {
            "results": [
                {"name": "Tomato", "confidence": 0.95},
                {"name": "Onion", "confidence": 0.88}
            ],
            "batch_id": "batch_123"
        }
        
        use_case = RecognizeBatchUseCase(ai_service=mock_ai_service)
        
        batch_data = {
            "images": ["image1.jpg", "image2.jpg"],
            "user_id": "user_123"
        }
        
        # Act
        result = use_case.execute(batch_data)
        
        # Assert
        assert len(result["results"]) == 2
        assert result["batch_id"] == "batch_123"
        mock_ai_service.recognize_batch.assert_called_once()

    # Auth Use Cases Tests
    def test_login_user_use_case_success(self):
        """Test login user use case successful execution"""
        # Arrange
        from src.application.use_cases.auth.login_user_usecase import LoginUserUseCase
        
        mock_auth_service = Mock()
        mock_auth_service.login.return_value = {
            "user_id": "user_123",
            "access_token": "jwt_token_here",
            "refresh_token": "refresh_token_here",
            "expires_in": 3600
        }
        
        use_case = LoginUserUseCase(auth_service=mock_auth_service)
        
        credentials = {
            "email": "test@example.com",
            "password": "SecurePass123!"
        }
        
        # Act
        result = use_case.execute(credentials)
        
        # Assert
        assert result["user_id"] == "user_123"
        assert "access_token" in result
        mock_auth_service.login.assert_called_once()

    def test_oauth_login_use_case_success(self):
        """Test OAuth login use case successful execution"""
        # Arrange
        from src.application.use_cases.auth.login_oauth_usecase import LoginOAuthUseCase
        
        mock_oauth_service = Mock()
        mock_oauth_service.authenticate_oauth.return_value = {
            "user_id": "oauth_user_123",
            "access_token": "oauth_jwt_token",
            "provider": "google"
        }
        
        use_case = LoginOAuthUseCase(oauth_service=mock_oauth_service)
        
        oauth_data = {
            "provider": "google",
            "code": "oauth_auth_code",
            "redirect_uri": "http://localhost:5000/callback"
        }
        
        # Act
        result = use_case.execute(oauth_data)
        
        # Assert
        assert result["user_id"] == "oauth_user_123"
        assert result["provider"] == "google"
        mock_oauth_service.authenticate_oauth.assert_called_once()

    # Planning Use Cases Tests
    def test_save_meal_plan_use_case_success(self):
        """Test save meal plan use case successful execution"""
        # Arrange
        from src.application.use_cases.planning.save_meal_plan_use_case import SaveMealPlanUseCase
        
        mock_planning_service = Mock()
        mock_planning_service.save_meal_plan.return_value = {
            "plan_id": 1,
            "user_id": "user_123",
            "date": "2024-01-15",
            "meals": {
                "breakfast": {"recipe_id": 1, "name": "Oatmeal"},
                "lunch": {"recipe_id": 2, "name": "Salad"},
                "dinner": {"recipe_id": 3, "name": "Pasta"}
            }
        }
        
        use_case = SaveMealPlanUseCase(planning_service=mock_planning_service)
        
        meal_plan_data = {
            "user_id": "user_123",
            "date": "2024-01-15",
            "meals": {
                "breakfast": {"recipe_id": 1},
                "lunch": {"recipe_id": 2},
                "dinner": {"recipe_id": 3}
            }
        }
        
        # Act
        result = use_case.execute(meal_plan_data)
        
        # Assert
        assert result["plan_id"] == 1
        assert result["date"] == "2024-01-15"
        mock_planning_service.save_meal_plan.assert_called_once()

    def test_get_meal_plan_by_user_and_date_use_case_success(self):
        """Test get meal plan by user and date use case successful execution"""
        # Arrange
        from src.application.use_cases.planning.get_meal_plan_by_user_and_date_use_case import GetMealPlanByUserAndDateUseCase
        
        mock_planning_repo = Mock()
        mock_planning_repo.get_by_user_and_date.return_value = {
            "plan_id": 1,
            "user_id": "user_123",
            "date": "2024-01-15",
            "meals": {
                "breakfast": "Oatmeal",
                "lunch": "Salad",
                "dinner": "Pasta"
            }
        }
        
        use_case = GetMealPlanByUserAndDateUseCase(planning_repository=mock_planning_repo)
        
        # Act
        result = use_case.execute(user_id="user_123", date="2024-01-15")
        
        # Assert
        assert result["plan_id"] == 1
        assert result["date"] == "2024-01-15"
        mock_planning_repo.get_by_user_and_date.assert_called_once_with("user_123", "2024-01-15")

    # Environmental Use Cases Tests
    def test_environmental_impact_calculation_use_case(self):
        """Test environmental impact calculation use case"""
        # Arrange
        from src.application.use_cases.recipes.calculate_environmental_savings_from_session import CalculateEnvironmentalSavingsFromSessionUseCase
        
        mock_env_service = Mock()
        mock_env_service.calculate_session_impact.return_value = {
            "co2_saved": 2.5,
            "water_saved": 150.0,
            "waste_prevented": 1.2
        }
        
        use_case = CalculateEnvironmentalSavingsFromSessionUseCase(environmental_service=mock_env_service)
        
        session_data = {
            "session_id": 1,
            "ingredients_used": ["Tomato", "Onion"],
            "portions_created": 4
        }
        
        # Act
        result = use_case.execute(session_data)
        
        # Assert
        assert result["co2_saved"] == 2.5
        assert result["water_saved"] == 150.0
        mock_env_service.calculate_session_impact.assert_called_once()

    # Image Management Use Cases Tests
    def test_upload_inventory_image_use_case_success(self):
        """Test upload inventory image use case successful execution"""
        # Arrange
        from src.application.use_cases.inventory.upload_inventory_image_use_case import UploadInventoryImageUseCase
        
        mock_storage_service = Mock()
        mock_storage_service.upload_image.return_value = {
            "image_url": "https://storage.example.com/image123.jpg",
            "image_id": "img_123"
        }
        
        use_case = UploadInventoryImageUseCase(storage_service=mock_storage_service)
        
        image_data = {
            "user_id": "user_123",
            "image_file": b"fake_image_data",
            "filename": "inventory_photo.jpg"
        }
        
        # Act
        result = use_case.execute(image_data)
        
        # Assert
        assert result["image_url"] == "https://storage.example.com/image123.jpg"
        assert result["image_id"] == "img_123"
        mock_storage_service.upload_image.assert_called_once()

    def test_batch_management_use_case_success(self):
        """Test batch management use case successful execution"""
        # Arrange
        from src.application.use_cases.inventory.batch_management_use_cases import BatchTransformUseCase
        
        mock_batch_service = Mock()
        mock_batch_service.transform_batch.return_value = {
            "batch_id": "batch_123",
            "status": "transformed",
            "items_processed": 5
        }
        
        use_case = BatchTransformUseCase(batch_service=mock_batch_service)
        
        batch_data = {
            "batch_id": "batch_123",
            "transformation_type": "ingredients_to_foods",
            "user_id": "user_123"
        }
        
        # Act
        result = use_case.execute(batch_data)
        
        # Assert
        assert result["status"] == "transformed"
        assert result["items_processed"] == 5
        mock_batch_service.transform_batch.assert_called_once()
