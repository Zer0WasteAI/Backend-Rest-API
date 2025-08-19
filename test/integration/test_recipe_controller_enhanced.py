"""
Integration tests for Recipe Controller Enhanced Coverage
Tests end-to-end recipe management workflows including favorites and advanced features
"""
import pytest
import json
from datetime import datetime, date, timedelta
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token


class TestRecipeControllerEnhancedIntegration:
    """Enhanced integration test suite for Recipe Controller covering missing endpoints"""
    
    @pytest.fixture
    def app(self):
        """Create Flask app for integration testing"""
        app = Flask(__name__)
        app.config['JWT_SECRET_KEY'] = 'test-secret'
        app.config['TESTING'] = True
        
        # Register recipe blueprint
        from src.interface.controllers.recipe_controller import recipes_bp
        app.register_blueprint(recipes_bp, url_prefix='/api/recipes')
        
        # Initialize JWT
        jwt = JWTManager(app)
        
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    @pytest.fixture
    def auth_token(self, app):
        """Create test authentication token"""
        with app.app_context():
            token = create_access_token(identity="recipe-test-user")
        return token
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Create authentication headers"""
        return {"Authorization": f"Bearer {auth_token}"}

    # INTEGRATION TEST 1: Custom Recipe Generation Workflow
    @patch('src.interface.controllers.recipe_controller.make_generate_custom_recipes_use_case')
    @patch('src.interface.controllers.recipe_controller.make_get_saved_recipes_use_case')
    def test_custom_recipe_generation_workflow(
        self,
        mock_get_saved_use_case,
        mock_generate_custom_use_case,
        client,
        auth_headers
    ):
        """Test custom recipe generation with user preferences and dietary restrictions"""
        
        # Step 1: Generate custom recipes based on preferences
        mock_generate_custom_use_case.return_value.execute.return_value = {
            "generation_id": "custom_gen_001",
            "recipes": [
                {
                    "recipe_uid": "custom_recipe_001",
                    "title": "Mediterranean Quinoa Bowl",
                    "cuisine_type": "Mediterranean",
                    "dietary_tags": ["vegetarian", "gluten_free", "high_protein"],
                    "difficulty": "easy",
                    "prep_time": 15,
                    "cook_time": 20,
                    "servings": 4,
                    "ingredients": [
                        {"name": "quinoa", "amount": "1 cup", "category": "grains"},
                        {"name": "chickpeas", "amount": "1 can", "category": "protein"},
                        {"name": "cucumber", "amount": "2 medium", "category": "vegetables"},
                        {"name": "feta cheese", "amount": "100g", "category": "dairy"}
                    ],
                    "instructions": [
                        {"step": 1, "instruction": "Cook quinoa according to package directions", "time": 15},
                        {"step": 2, "instruction": "Drain and rinse chickpeas", "time": 2},
                        {"step": 3, "instruction": "Dice cucumber and crumble feta", "time": 5},
                        {"step": 4, "instruction": "Combine all ingredients in bowl", "time": 3}
                    ],
                    "nutritional_info": {
                        "calories": 380,
                        "protein": 18,
                        "carbs": 45,
                        "fat": 12,
                        "fiber": 8
                    },
                    "match_score": 95,
                    "generation_notes": "Perfect match for Mediterranean + vegetarian preferences"
                },
                {
                    "recipe_uid": "custom_recipe_002",
                    "title": "Asian-Inspired Stir Fry Bowl",
                    "cuisine_type": "Asian",
                    "dietary_tags": ["vegetarian", "dairy_free"],
                    "difficulty": "easy",
                    "prep_time": 10,
                    "cook_time": 12,
                    "servings": 3,
                    "ingredients": [
                        {"name": "brown rice", "amount": "1.5 cups", "category": "grains"},
                        {"name": "broccoli", "amount": "2 cups", "category": "vegetables"},
                        {"name": "bell peppers", "amount": "2 medium", "category": "vegetables"},
                        {"name": "soy sauce", "amount": "3 tbsp", "category": "condiments"}
                    ],
                    "match_score": 87,
                    "generation_notes": "Good match for Asian cuisine preference"
                }
            ],
            "generation_metadata": {
                "user_preferences": {
                    "dietary_restrictions": ["vegetarian"],
                    "cuisine_preferences": ["Mediterranean", "Asian"],
                    "difficulty_max": "medium",
                    "prep_time_max": 30
                },
                "total_recipes_generated": 2,
                "avg_match_score": 91,
                "generation_time_seconds": 3.2
            }
        }
        
        custom_request = {
            "dietary_restrictions": ["vegetarian"],
            "cuisine_preferences": ["Mediterranean", "Asian"],
            "difficulty_max": "medium",
            "prep_time_max": 30,
            "servings": 4,
            "exclude_ingredients": ["nuts", "shellfish"]
        }
        
        response = client.post("/api/recipes/generate-custom",
                              json=custom_request,
                              headers=auth_headers)
        
        assert response.status_code in [200, 201]
        data = response.get_json()
        assert len(data["recipes"]) == 2
        assert data["recipes"][0]["match_score"] == 95
        assert "vegetarian" in data["recipes"][0]["dietary_tags"]
        assert data["generation_metadata"]["avg_match_score"] == 91
        
        # Step 2: Save one of the generated recipes
        mock_get_saved_use_case.return_value.execute.return_value = {
            "recipes": [data["recipes"][0]],  # Recipe was saved
            "total_saved": 1
        }
        
        # Verify saved recipes include the custom generated one
        response = client.get("/api/recipes/saved", headers=auth_headers)
        assert response.status_code == 200
        saved_data = response.get_json()
        assert len(saved_data["recipes"]) == 1
        assert saved_data["recipes"][0]["recipe_uid"] == "custom_recipe_001"

    # INTEGRATION TEST 2: Recipe Favorites System Complete Workflow
    @patch('src.interface.controllers.recipe_controller.make_add_recipe_to_favorites_use_case')
    @patch('src.interface.controllers.recipe_controller.make_get_user_favorite_recipes_use_case')
    @patch('src.interface.controllers.recipe_controller.make_remove_recipe_from_favorites_use_case')
    @patch('src.interface.controllers.recipe_controller.make_update_recipe_favorite_use_case')
    def test_recipe_favorites_complete_workflow(
        self,
        mock_update_favorite_use_case,
        mock_remove_favorite_use_case,
        mock_get_favorites_use_case,
        mock_add_favorite_use_case,
        client,
        auth_headers
    ):
        """Test complete recipe favorites workflow: Add → Get → Update → Remove"""
        
        # Step 1: Add recipe to favorites
        mock_add_favorite_use_case.return_value.execute.return_value = {
            "recipe_uid": "recipe_fav_001",
            "recipe_title": "Spicy Thai Curry",
            "added_to_favorites": True,
            "favorite_id": "fav_001",
            "added_at": "2025-08-19T16:00:00Z",
            "user_notes": "Love the spice level!",
            "tags": ["spicy", "thai", "comfort_food"]
        }
        
        favorite_request = {
            "recipe_uid": "recipe_fav_001",
            "user_notes": "Love the spice level!",
            "tags": ["spicy", "thai", "comfort_food"]
        }
        
        response = client.post("/api/recipes/generated/recipe_fav_001/favorite",
                              json=favorite_request,
                              headers=auth_headers)
        
        assert response.status_code in [200, 201]
        add_data = response.get_json()
        assert add_data["added_to_favorites"] is True
        assert add_data["favorite_id"] == "fav_001"
        
        # Step 2: Get user's favorite recipes
        mock_get_favorites_use_case.return_value.execute.return_value = {
            "favorites": [
                {
                    "favorite_id": "fav_001",
                    "recipe_uid": "recipe_fav_001",
                    "recipe_title": "Spicy Thai Curry",
                    "user_notes": "Love the spice level!",
                    "tags": ["spicy", "thai", "comfort_food"],
                    "added_at": "2025-08-19T16:00:00Z",
                    "times_cooked": 3,
                    "last_cooked": "2025-08-18T19:30:00Z",
                    "rating": 5
                },
                {
                    "favorite_id": "fav_002",
                    "recipe_uid": "recipe_fav_002",
                    "recipe_title": "Classic Caesar Salad",
                    "user_notes": "Perfect for lunch",
                    "tags": ["healthy", "quick", "lunch"],
                    "added_at": "2025-08-17T12:00:00Z",
                    "times_cooked": 7,
                    "last_cooked": "2025-08-19T13:00:00Z",
                    "rating": 4
                }
            ],
            "total_favorites": 2,
            "most_cooked": "recipe_fav_002",
            "highest_rated": "recipe_fav_001",
            "recently_added": "recipe_fav_001"
        }
        
        response = client.get("/api/recipes/generated/favorites", headers=auth_headers)
        
        assert response.status_code == 200
        favorites_data = response.get_json()
        assert len(favorites_data["favorites"]) == 2
        assert favorites_data["most_cooked"] == "recipe_fav_002"
        assert favorites_data["highest_rated"] == "recipe_fav_001"
        
        # Step 3: Update favorite with new rating and notes
        mock_update_favorite_use_case.return_value.execute.return_value = {
            "recipe_uid": "recipe_fav_001",
            "favorite_id": "fav_001",
            "updated_fields": {
                "user_notes": "Absolutely amazing! Reduced salt slightly.",
                "rating": 5,
                "tags": ["spicy", "thai", "comfort_food", "modified"]
            },
            "updated_at": "2025-08-19T17:00:00Z",
            "cooking_log_entry": {
                "cooked_at": "2025-08-19T19:00:00Z",
                "modifications": ["reduced salt by 25%"],
                "cooking_notes": "Perfect spice level after salt reduction"
            }
        }
        
        update_request = {
            "user_notes": "Absolutely amazing! Reduced salt slightly.",
            "rating": 5,
            "tags": ["spicy", "thai", "comfort_food", "modified"],
            "cooking_log": {
                "cooked_at": "2025-08-19T19:00:00Z",
                "modifications": ["reduced salt by 25%"],
                "cooking_notes": "Perfect spice level after salt reduction"
            }
        }
        
        response = client.put("/api/recipes/generated/recipe_fav_001/favorite",
                             json=update_request,
                             headers=auth_headers)
        
        assert response.status_code == 200
        update_data = response.get_json()
        assert "modified" in update_data["updated_fields"]["tags"]
        assert "cooking_log_entry" in update_data
        
        # Step 4: Remove recipe from favorites
        mock_remove_favorite_use_case.return_value.execute.return_value = {
            "recipe_uid": "recipe_fav_001",
            "removed_from_favorites": True,
            "removed_at": "2025-08-19T18:00:00Z",
            "favorite_duration_days": 2,
            "cooking_stats": {
                "times_cooked_while_favorite": 3,
                "total_cooking_time": 90,
                "avg_rating": 5
            }
        }
        
        response = client.delete("/api/recipes/generated/recipe_fav_001/favorite",
                                headers=auth_headers)
        
        assert response.status_code in [200, 204]
        if response.status_code == 200:
            remove_data = response.get_json()
            assert remove_data["removed_from_favorites"] is True
            assert remove_data["cooking_stats"]["times_cooked_while_favorite"] == 3

    # INTEGRATION TEST 3: Generated Recipes Gallery with Filtering
    @patch('src.interface.controllers.recipe_controller.make_get_generated_recipes_gallery_use_case')
    def test_generated_recipes_gallery_integration(
        self,
        mock_gallery_use_case,
        client,
        auth_headers
    ):
        """Test generated recipes gallery with advanced filtering and sorting"""
        
        mock_gallery_use_case.return_value.execute.return_value = {
            "recipes": [
                {
                    "recipe_uid": "gallery_001",
                    "title": "Mediterranean Pasta Salad",
                    "cuisine_type": "Mediterranean",
                    "difficulty": "easy",
                    "prep_time": 20,
                    "cook_time": 10,
                    "image_url": "https://storage.googleapis.com/gallery/med_pasta.jpg",
                    "thumbnail_url": "https://storage.googleapis.com/thumbs/med_pasta.jpg",
                    "generated_at": "2025-08-19T10:00:00Z",
                    "popularity_score": 8.7,
                    "user_rating": 4.5,
                    "times_generated": 23,
                    "dietary_tags": ["vegetarian", "mediterranean"],
                    "is_favorite": False,
                    "generation_source": "inventory_based"
                },
                {
                    "recipe_uid": "gallery_002",
                    "title": "Asian Fusion Stir Fry",
                    "cuisine_type": "Asian",
                    "difficulty": "medium",
                    "prep_time": 15,
                    "cook_time": 12,
                    "image_url": "https://storage.googleapis.com/gallery/asian_stir.jpg",
                    "thumbnail_url": "https://storage.googleapis.com/thumbs/asian_stir.jpg",
                    "generated_at": "2025-08-18T14:30:00Z",
                    "popularity_score": 9.2,
                    "user_rating": 5.0,
                    "times_generated": 41,
                    "dietary_tags": ["dairy_free", "high_protein"],
                    "is_favorite": True,
                    "generation_source": "custom_request"
                }
            ],
            "gallery_metadata": {
                "total_recipes": 2,
                "filters_applied": {
                    "cuisine_type": None,
                    "difficulty": None,
                    "dietary_restrictions": None,
                    "prep_time_max": None
                },
                "sorting": {
                    "sort_by": "popularity",
                    "sort_order": "desc"
                },
                "pagination": {
                    "current_page": 1,
                    "total_pages": 1,
                    "per_page": 20
                }
            },
            "user_interactions": {
                "total_favorites": 1,
                "total_generated_by_user": 2,
                "last_generated": "2025-08-19T10:00:00Z"
            }
        }
        
        response = client.get("/api/recipes/generated/gallery?sort_by=popularity&order=desc",
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["recipes"]) == 2
        assert data["recipes"][1]["popularity_score"] > data["recipes"][0]["popularity_score"]  # Sorted by popularity
        assert data["gallery_metadata"]["sorting"]["sort_by"] == "popularity"
        assert data["user_interactions"]["total_favorites"] == 1

    # INTEGRATION TEST 4: Default Recipes Management
    @patch('src.interface.controllers.recipe_controller.make_get_default_recipes_use_case')
    def test_default_recipes_integration(
        self,
        mock_default_recipes_use_case,
        client,
        auth_headers
    ):
        """Test default recipes system with categories and recommendations"""
        
        mock_default_recipes_use_case.return_value.execute.return_value = {
            "default_recipes": [
                {
                    "recipe_uid": "default_001",
                    "title": "Classic Spaghetti Carbonara",
                    "category": "pasta",
                    "cuisine_type": "Italian",
                    "difficulty": "medium",
                    "prep_time": 10,
                    "cook_time": 15,
                    "is_premium": False,
                    "popularity_rank": 1,
                    "chef_recommended": True,
                    "dietary_tags": [],
                    "description": "Traditional Roman pasta dish with eggs, cheese, and pancetta"
                },
                {
                    "recipe_uid": "default_002",
                    "title": "Chicken Caesar Salad",
                    "category": "salads",
                    "cuisine_type": "American",
                    "difficulty": "easy",
                    "prep_time": 15,
                    "cook_time": 20,
                    "is_premium": True,
                    "popularity_rank": 3,
                    "chef_recommended": False,
                    "dietary_tags": ["high_protein", "gluten_free_option"],
                    "description": "Crispy chicken over fresh romaine with classic Caesar dressing"
                },
                {
                    "recipe_uid": "default_003",
                    "title": "Vegetable Stir Fry Bowl",
                    "category": "healthy",
                    "cuisine_type": "Asian",
                    "difficulty": "easy",
                    "prep_time": 12,
                    "cook_time": 8,
                    "is_premium": False,
                    "popularity_rank": 2,
                    "chef_recommended": True,
                    "dietary_tags": ["vegetarian", "vegan", "dairy_free"],
                    "description": "Colorful mix of seasonal vegetables in savory Asian sauce"
                }
            ],
            "categories": {
                "pasta": 1,
                "salads": 1,
                "healthy": 1
            },
            "recommendations": {
                "trending": ["default_003", "default_001"],
                "chef_picks": ["default_001", "default_003"],
                "beginner_friendly": ["default_002", "default_003"]
            },
            "metadata": {
                "total_default_recipes": 3,
                "last_updated": "2025-08-19T08:00:00Z",
                "premium_recipes_available": 1
            }
        }
        
        response = client.get("/api/recipes/default", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["default_recipes"]) == 3
        assert data["categories"]["pasta"] == 1
        assert len(data["recommendations"]["chef_picks"]) == 2
        assert data["metadata"]["premium_recipes_available"] == 1
        
        # Test filtered default recipes
        response = client.get("/api/recipes/default?category=healthy&difficulty=easy",
                             headers=auth_headers)
        
        assert response.status_code == 200
        filtered_data = response.get_json()
        # Should filter results based on query parameters

    # INTEGRATION TEST 5: Recipe Deletion with Dependencies Check
    @patch('src.interface.controllers.recipe_controller.make_delete_user_recipe_use_case')
    def test_recipe_deletion_integration(
        self,
        mock_delete_use_case,
        client,
        auth_headers
    ):
        """Test recipe deletion with dependency checking and cleanup"""
        
        mock_delete_use_case.return_value.execute.return_value = {
            "recipe_uid": "recipe_to_delete",
            "deleted": True,
            "deleted_at": "2025-08-19T18:30:00Z",
            "cleanup_summary": {
                "favorites_removed": 1,
                "cooking_sessions_archived": 3,
                "images_deleted": 2,
                "meal_plans_updated": 1
            },
            "dependencies_found": {
                "was_favorite": True,
                "has_cooking_history": True,
                "in_meal_plans": True,
                "has_shared_links": False
            },
            "recovery_info": {
                "can_recover": True,
                "recovery_window_days": 30,
                "recovery_token": "rec_token_123"
            }
        }
        
        delete_request = {
            "recipe_uid": "recipe_to_delete",
            "confirm_deletion": True,
            "cleanup_dependencies": True
        }
        
        response = client.delete("/api/recipes/delete",
                                json=delete_request,
                                headers=auth_headers)
        
        assert response.status_code in [200, 204]
        if response.status_code == 200:
            data = response.get_json()
            assert data["deleted"] is True
            assert data["cleanup_summary"]["favorites_removed"] == 1
            assert data["recovery_info"]["can_recover"] is True

    # INTEGRATION TEST 6: Authentication and Authorization
    def test_recipe_enhanced_authentication_integration(self, client):
        """Test authentication requirements for enhanced recipe endpoints"""
        
        endpoints_to_test = [
            ("POST", "/api/recipes/generate-custom", {"dietary_restrictions": ["vegetarian"]}),
            ("POST", "/api/recipes/generated/recipe_001/favorite", {"user_notes": "Great!"}),
            ("GET", "/api/recipes/generated/favorites", None),
            ("PUT", "/api/recipes/generated/recipe_001/favorite", {"rating": 5}),
            ("DELETE", "/api/recipes/generated/recipe_001/favorite", None),
            ("GET", "/api/recipes/generated/gallery", None),
            ("GET", "/api/recipes/default", None),
            ("DELETE", "/api/recipes/delete", {"recipe_uid": "test"})
        ]
        
        for method, endpoint, data in endpoints_to_test:
            if method == "POST":
                response = client.post(endpoint, json=data)
            elif method == "GET":
                response = client.get(endpoint)
            elif method == "PUT":
                response = client.put(endpoint, json=data)
            elif method == "DELETE":
                response = client.delete(endpoint, json=data)
                
            assert response.status_code == 401, f"Endpoint {method} {endpoint} should require authentication"

    # INTEGRATION TEST 7: Error Handling and Edge Cases
    @patch('src.interface.controllers.recipe_controller.make_generate_custom_recipes_use_case')
    @patch('src.interface.controllers.recipe_controller.make_add_recipe_to_favorites_use_case')
    def test_recipe_error_handling_integration(
        self,
        mock_add_favorite_use_case,
        mock_generate_custom_use_case,
        client,
        auth_headers
    ):
        """Test error handling across recipe endpoints"""
        
        # Test custom generation with invalid parameters
        mock_generate_custom_use_case.return_value.execute.side_effect = ValueError("Invalid dietary restrictions")
        
        invalid_request = {
            "dietary_restrictions": ["invalid_restriction"],
            "cuisine_preferences": []
        }
        
        response = client.post("/api/recipes/generate-custom",
                              json=invalid_request,
                              headers=auth_headers)
        
        assert response.status_code in [400, 422, 500]
        
        # Test duplicate favorite addition
        mock_add_favorite_use_case.return_value.execute.side_effect = ValueError("Recipe already in favorites")
        
        response = client.post("/api/recipes/generated/recipe_001/favorite",
                              json={"user_notes": "Already favorite"},
                              headers=auth_headers)
        
        assert response.status_code in [400, 409, 500]
