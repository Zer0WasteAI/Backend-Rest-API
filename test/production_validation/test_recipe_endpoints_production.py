"""
Production Validation Tests for Recipe Management Endpoints
Tests all recipe endpoints including generation, saving, favorites, and management
"""
import pytest
import json
import time
from unittest.mock import patch, MagicMock
from src.main import create_app


class TestRecipeEndpointsProduction:
    """Production validation tests for all recipe management endpoints"""

    @pytest.fixture(scope="class")
    def app(self):
        app = create_app()
        app.config.update({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "JWT_ACCESS_TOKEN_EXPIRES": False,
        })
        return app

    @pytest.fixture
    def client(self, app):
        return app.test_client()

    @pytest.fixture
    def auth_headers(self, app):
        with app.app_context():
            from flask_jwt_extended import create_access_token
            token = create_access_token(identity="test-user-uid")
            return {"Authorization": f"Bearer {token}"}

    # ================================================================
    # POST /api/recipes/generate-from-inventory - Generate Recipes from Inventory
    # ================================================================

    def test_generate_recipes_from_inventory_success(self, client, auth_headers):
        """Test successful recipe generation from inventory"""
        with patch('src.application.use_cases.recipes.generate_recipes_use_case.GenerateRecipesUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "recipes": [
                    {
                        "title": "Tomato Basil Pasta",
                        "ingredients": ["tomato", "basil", "pasta"],
                        "instructions": ["Boil pasta", "Add tomatoes", "Mix with basil"],
                        "cooking_time": "20 minutes",
                        "difficulty": "easy",
                        "servings": 2
                    },
                    {
                        "title": "Vegetable Stir Fry",
                        "ingredients": ["tomato", "onion", "bell pepper"],
                        "instructions": ["Heat oil", "Add vegetables", "Stir fry"],
                        "cooking_time": "15 minutes",
                        "difficulty": "easy",
                        "servings": 1
                    }
                ],
                "generation_id": "gen_12345",
                "total_recipes": 2
            }

            generation_data = {
                "dietary_restrictions": ["vegetarian"],
                "max_recipes": 3,
                "difficulty_level": "easy",
                "cooking_time_max": 30
            }

            response = client.post('/api/recipes/generate-from-inventory',
                json=generation_data,
                headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['total_recipes'] == 2
            assert len(data['recipes']) == 2
            assert 'generation_id' in data

    def test_generate_recipes_empty_inventory(self, client, auth_headers):
        """Test recipe generation with empty inventory"""
        with patch('src.application.use_cases.recipes.generate_recipes_use_case.GenerateRecipesUseCase.execute') as mock_execute:
            mock_execute.side_effect = Exception("No ingredients available in inventory")

            response = client.post('/api/recipes/generate-from-inventory',
                json={},
                headers=auth_headers)

            assert response.status_code == 400

    def test_generate_recipes_rate_limiting(self, client, auth_headers):
        """Test rate limiting on recipe generation (ai_recipe_generation: 8 req/min)"""
        with patch('src.application.use_cases.recipes.generate_recipes_use_case.GenerateRecipesUseCase.execute'):
            for i in range(10):
                response = client.post('/api/recipes/generate-from-inventory',
                    json={},
                    headers=auth_headers)
                
                if i < 8:
                    assert response.status_code in [200, 400]
                else:
                    assert response.status_code == 429

    def test_generate_recipes_invalid_dietary_restrictions(self, client, auth_headers):
        """Test recipe generation with invalid dietary restrictions"""
        invalid_data = {
            "dietary_restrictions": ["invalid_restriction"],
            "max_recipes": 5
        }

        response = client.post('/api/recipes/generate-from-inventory',
            json=invalid_data,
            headers=auth_headers)

        assert response.status_code in [400, 422]

    def test_generate_recipes_performance(self, client, auth_headers):
        """Test recipe generation performance"""
        with patch('src.application.use_cases.recipes.generate_recipes_use_case.GenerateRecipesUseCase.execute') as mock_execute:
            mock_execute.return_value = {"recipes": [], "total_recipes": 0}

            start_time = time.time()
            response = client.post('/api/recipes/generate-from-inventory',
                json={},
                headers=auth_headers)
            end_time = time.time()

            response_time = end_time - start_time
            
            # Recipe generation should complete within 30 seconds
            assert response_time < 30.0
            assert response.status_code == 200

    # ================================================================
    # POST /api/recipes/generate-custom - Generate Custom Recipes
    # ================================================================

    def test_generate_custom_recipes_success(self, client, auth_headers):
        """Test successful custom recipe generation"""
        with patch('src.application.use_cases.recipes.generate_custom_recipe_use_case.GenerateCustomRecipeUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "recipe": {
                    "title": "Custom Chicken Pasta",
                    "ingredients": ["chicken", "pasta", "tomato sauce"],
                    "instructions": ["Cook chicken", "Boil pasta", "Combine with sauce"],
                    "cooking_time": "25 minutes",
                    "difficulty": "medium",
                    "servings": 4
                },
                "recipe_id": "recipe_custom_123"
            }

            custom_data = {
                "ingredients": ["chicken", "pasta", "tomato sauce"],
                "dietary_restrictions": [],
                "cuisine_type": "italian",
                "cooking_time_max": 30,
                "difficulty_level": "medium"
            }

            response = client.post('/api/recipes/generate-custom',
                json=custom_data,
                headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert 'recipe' in data
            assert data['recipe']['title'] == "Custom Chicken Pasta"

    def test_generate_custom_recipes_missing_ingredients(self, client, auth_headers):
        """Test custom recipe generation without ingredients"""
        response = client.post('/api/recipes/generate-custom',
            json={"dietary_restrictions": []},
            headers=auth_headers)

        assert response.status_code == 400

    def test_generate_custom_recipes_empty_ingredients(self, client, auth_headers):
        """Test custom recipe generation with empty ingredients list"""
        response = client.post('/api/recipes/generate-custom',
            json={"ingredients": []},
            headers=auth_headers)

        assert response.status_code == 400

    # ================================================================
    # POST /api/recipes/generate-save-from-inventory - Generate and Save Recipes
    # ================================================================

    def test_generate_save_recipes_success(self, client, auth_headers):
        """Test successful recipe generation and saving"""
        with patch('src.application.use_cases.recipes.generate_recipes_use_case.GenerateRecipesUseCase.execute') as mock_generate:
            with patch('src.application.use_cases.recipes.save_recipe_use_case.SaveRecipeUseCase.execute') as mock_save:
                mock_generate.return_value = {
                    "recipes": [
                        {
                            "title": "Saved Recipe",
                            "ingredients": ["tomato", "basil"],
                            "instructions": ["Step 1", "Step 2"]
                        }
                    ],
                    "generation_id": "gen_save_123"
                }
                
                mock_save.return_value = {
                    "message": "Recipes saved successfully",
                    "saved_count": 1,
                    "recipe_ids": ["recipe_123"]
                }

                response = client.post('/api/recipes/generate-save-from-inventory',
                    json={"auto_save": True},
                    headers=auth_headers)

                assert response.status_code == 200
                data = response.get_json()
                assert data['saved_count'] == 1

    # ================================================================
    # GET /api/recipes/saved - Get User's Saved Recipes
    # ================================================================

    def test_get_saved_recipes_success(self, client, auth_headers):
        """Test getting user's saved recipes"""
        with patch('src.application.use_cases.recipes.get_saved_recipes_use_case.GetSavedRecipesUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "recipes": [
                    {
                        "uid": "recipe_123",
                        "title": "Tomato Pasta",
                        "ingredients": ["tomato", "pasta"],
                        "cooking_time": "20 minutes",
                        "difficulty": "easy",
                        "is_favorite": True,
                        "created_at": "2024-01-10T10:00:00Z"
                    }
                ],
                "total_count": 1
            }

            response = client.get('/api/recipes/saved', headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['total_count'] == 1
            assert len(data['recipes']) == 1

    def test_get_saved_recipes_pagination(self, client, auth_headers):
        """Test saved recipes with pagination"""
        with patch('src.application.use_cases.recipes.get_saved_recipes_use_case.GetSavedRecipesUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "recipes": [{"uid": f"recipe_{i}", "title": f"Recipe {i}"} for i in range(10)],
                "total_count": 25,
                "page": 1,
                "per_page": 10
            }

            response = client.get('/api/recipes/saved?page=1&per_page=10', headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['total_count'] == 25
            assert len(data['recipes']) == 10

    def test_get_saved_recipes_empty(self, client, auth_headers):
        """Test getting saved recipes when user has none"""
        with patch('src.application.use_cases.recipes.get_saved_recipes_use_case.GetSavedRecipesUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "recipes": [],
                "total_count": 0
            }

            response = client.get('/api/recipes/saved', headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['total_count'] == 0

    # ================================================================
    # GET /api/recipes/all - Get All Available Recipes
    # ================================================================

    def test_get_all_recipes_success(self, client, auth_headers):
        """Test getting all available recipes"""
        with patch('src.application.use_cases.recipes.get_all_recipes_use_case.GetAllRecipesUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "recipes": [
                    {"title": "Public Recipe 1", "category": "vegetarian"},
                    {"title": "Public Recipe 2", "category": "meat"}
                ],
                "total_count": 2,
                "categories": ["vegetarian", "meat"]
            }

            response = client.get('/api/recipes/all', headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['total_count'] == 2
            assert 'categories' in data

    def test_get_all_recipes_filtering(self, client, auth_headers):
        """Test getting all recipes with category filtering"""
        with patch('src.application.use_cases.recipes.get_all_recipes_use_case.GetAllRecipesUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "recipes": [{"title": "Vegetarian Recipe", "category": "vegetarian"}],
                "total_count": 1
            }

            response = client.get('/api/recipes/all?category=vegetarian', headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['total_count'] == 1

    # ================================================================
    # Recipe Generation Gallery and Default Recipes
    # ================================================================

    def test_get_generated_recipes_gallery(self, client, auth_headers):
        """Test getting generated recipes gallery"""
        with patch('src.application.use_cases.recipes.get_saved_recipes_use_case.GetSavedRecipesUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "recipes": [
                    {
                        "uid": "gen_recipe_123",
                        "title": "Generated Recipe",
                        "image_url": "https://example.com/recipe.jpg",
                        "generation_id": "gen_123"
                    }
                ],
                "total_count": 1
            }

            response = client.get('/api/recipes/generated/gallery', headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['total_count'] == 1

    def test_get_default_recipes(self, client, auth_headers):
        """Test getting default/system recipes"""
        with patch('src.application.use_cases.recipes.get_all_recipes_use_case.GetAllRecipesUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "recipes": [
                    {"title": "Basic Pasta", "is_default": True},
                    {"title": "Simple Salad", "is_default": True}
                ],
                "total_count": 2
            }

            response = client.get('/api/recipes/default', headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['total_count'] == 2

    # ================================================================
    # Recipe Deletion
    # ================================================================

    def test_delete_user_recipe_success(self, client, auth_headers):
        """Test successful recipe deletion"""
        with patch('src.application.use_cases.recipes.delete_user_recipe_use_case.DeleteUserRecipeUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "message": "Recipe deleted successfully",
                "recipe_uid": "recipe_123"
            }

            response = client.delete('/api/recipes/delete?recipe_uid=recipe_123',
                headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['recipe_uid'] == 'recipe_123'

    def test_delete_recipe_missing_uid(self, client, auth_headers):
        """Test recipe deletion without recipe UID"""
        response = client.delete('/api/recipes/delete',
            headers=auth_headers)

        assert response.status_code == 400

    def test_delete_recipe_not_found(self, client, auth_headers):
        """Test deleting non-existent recipe"""
        with patch('src.application.use_cases.recipes.delete_user_recipe_use_case.DeleteUserRecipeUseCase.execute') as mock_execute:
            mock_execute.side_effect = Exception("Recipe not found")

            response = client.delete('/api/recipes/delete?recipe_uid=nonexistent',
                headers=auth_headers)

            assert response.status_code == 404

    def test_delete_recipe_unauthorized_user(self, client, auth_headers):
        """Test deleting recipe by different user"""
        with patch('src.application.use_cases.recipes.delete_user_recipe_use_case.DeleteUserRecipeUseCase.execute') as mock_execute:
            mock_execute.side_effect = Exception("Unauthorized access")

            response = client.delete('/api/recipes/delete?recipe_uid=other_user_recipe',
                headers=auth_headers)

            assert response.status_code in [403, 404]

    # ================================================================
    # Favorites Management
    # ================================================================

    def test_add_recipe_to_favorites_success(self, client, auth_headers):
        """Test adding recipe to favorites"""
        with patch('src.application.use_cases.recipes.save_recipe_use_case.SaveRecipeUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "message": "Recipe added to favorites",
                "recipe_uid": "recipe_123",
                "is_favorite": True
            }

            response = client.post('/api/recipes/generated/recipe_123/favorite',
                headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['is_favorite'] == True

    def test_remove_recipe_from_favorites_success(self, client, auth_headers):
        """Test removing recipe from favorites"""
        with patch('src.application.use_cases.recipes.save_recipe_use_case.SaveRecipeUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "message": "Recipe removed from favorites",
                "recipe_uid": "recipe_123",
                "is_favorite": False
            }

            response = client.delete('/api/recipes/generated/recipe_123/favorite',
                headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['is_favorite'] == False

    def test_update_favorite_status_success(self, client, auth_headers):
        """Test updating favorite status"""
        with patch('src.application.use_cases.recipes.save_recipe_use_case.SaveRecipeUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "message": "Favorite status updated",
                "recipe_uid": "recipe_123",
                "is_favorite": True
            }

            response = client.put('/api/recipes/generated/recipe_123/favorite',
                json={"is_favorite": True},
                headers=auth_headers)

            assert response.status_code == 200

    def test_get_favorite_recipes(self, client, auth_headers):
        """Test getting user's favorite recipes"""
        with patch('src.application.use_cases.recipes.get_saved_recipes_use_case.GetSavedRecipesUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "recipes": [
                    {
                        "uid": "recipe_123",
                        "title": "Favorite Recipe",
                        "is_favorite": True
                    }
                ],
                "total_count": 1
            }

            response = client.get('/api/recipes/generated/favorites', headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['total_count'] == 1

    # ================================================================
    # Security and Edge Case Tests
    # ================================================================

    def test_recipe_endpoints_security_headers(self, client, auth_headers):
        """Test security headers on recipe endpoints"""
        response = client.get('/api/recipes/saved', headers=auth_headers)
        
        assert 'X-Content-Type-Options' in response.headers
        assert 'X-Frame-Options' in response.headers

    def test_recipe_sql_injection_protection(self, client, auth_headers):
        """Test SQL injection protection in recipe endpoints"""
        malicious_uid = "'; DROP TABLE recipes; --"
        
        response = client.delete(f'/api/recipes/delete?recipe_uid={malicious_uid}',
            headers=auth_headers)
        
        assert response.status_code in [400, 404]

    def test_recipe_xss_protection(self, client, auth_headers):
        """Test XSS protection in recipe data"""
        xss_ingredients = ["<script>alert('xss')</script>", "tomato"]
        
        response = client.post('/api/recipes/generate-custom',
            json={"ingredients": xss_ingredients},
            headers=auth_headers)
        
        # Should handle XSS attempts safely
        data = response.get_data(as_text=True)
        assert '<script>' not in data

    def test_recipe_large_ingredient_list(self, client, auth_headers):
        """Test handling large ingredient lists"""
        large_ingredients = [f"ingredient_{i}" for i in range(100)]
        
        response = client.post('/api/recipes/generate-custom',
            json={"ingredients": large_ingredients},
            headers=auth_headers)
        
        # Should handle large lists gracefully
        assert response.status_code in [200, 400, 413]

    def test_recipe_concurrent_generation(self, client, auth_headers):
        """Test concurrent recipe generation requests"""
        import threading
        results = []
        
        def generate_recipe():
            response = client.post('/api/recipes/generate-from-inventory',
                json={},
                headers=auth_headers)
            results.append(response.status_code)
        
        with patch('src.application.use_cases.recipes.generate_recipes_use_case.GenerateRecipesUseCase.execute'):
            threads = []
            for _ in range(3):
                thread = threading.Thread(target=generate_recipe)
                threads.append(thread)
                thread.start()
            
            for thread in threads:
                thread.join()
        
        # All should complete without server errors
        assert all(status < 500 for status in results)

    def test_recipe_generation_timeout_handling(self, client, auth_headers):
        """Test recipe generation timeout handling"""
        with patch('src.application.use_cases.recipes.generate_recipes_use_case.GenerateRecipesUseCase.execute') as mock_execute:
            # Simulate long running operation
            import time
            def slow_execute(*args, **kwargs):
                time.sleep(0.1)  # Short delay for testing
                return {"recipes": [], "total_recipes": 0}
            
            mock_execute.side_effect = slow_execute
            
            response = client.post('/api/recipes/generate-from-inventory',
                json={},
                headers=auth_headers)
            
            # Should handle timeouts gracefully
            assert response.status_code in [200, 408, 504]

    def test_recipe_cache_performance(self, client, auth_headers):
        """Test recipe caching for performance"""
        with patch('src.application.use_cases.recipes.get_all_recipes_use_case.GetAllRecipesUseCase.execute') as mock_execute:
            mock_execute.return_value = {"recipes": [], "total_count": 0}

            # First request
            start_time = time.time()
            response1 = client.get('/api/recipes/all', headers=auth_headers)
            first_time = time.time() - start_time

            # Second request (should be faster due to caching)
            start_time = time.time()
            response2 = client.get('/api/recipes/all', headers=auth_headers)
            second_time = time.time() - start_time

            assert response1.status_code == 200
            assert response2.status_code == 200
            # Cache should make second request faster (or at least not significantly slower)
            assert second_time <= first_time * 2

    def test_recipe_memory_usage_large_responses(self, client, auth_headers):
        """Test memory usage with large recipe responses"""
        with patch('src.application.use_cases.recipes.get_all_recipes_use_case.GetAllRecipesUseCase.execute') as mock_execute:
            # Simulate large recipe database
            large_recipes = [
                {
                    "title": f"Recipe {i}",
                    "ingredients": [f"ingredient_{j}" for j in range(20)],
                    "instructions": [f"Step {k}" for k in range(10)]
                }
                for i in range(100)
            ]
            mock_execute.return_value = {
                "recipes": large_recipes,
                "total_count": 100
            }

            response = client.get('/api/recipes/all', headers=auth_headers)

            # Should handle large responses without memory issues
            assert response.status_code == 200
            data = response.get_json()
            assert len(data['recipes']) == 100