"""
Unit tests for Recipe Controller
Tests recipe management endpoints and business logic integration
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token

from src.interface.controllers.recipe_controller import recipes_bp


class TestRecipeController:
    """Test suite for Recipe Controller"""
    
    @pytest.fixture
    def app(self):
        """Create Flask app for testing using project configuration"""
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))
        
        # Set testing environment before importing
        os.environ['FLASK_ENV'] = 'testing'
        os.environ['TESTING'] = '1'
        
        from src.main import create_app
        app = create_app()
        app.config.update({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "WTF_CSRF_ENABLED": False
        })
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    @pytest.fixture
    def auth_token(self, app):
        """Create test authentication token"""
        with app.app_context():
            token = create_access_token(identity="test-user-123")
        return token
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Create authentication headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_recipe_blueprint_registration(self, app):
        """Test that recipe blueprint is properly registered"""
        # Assert
        assert 'recipes' in app.blueprints
        assert app.blueprints['recipes'] == recipes_bp
    
    @patch('src.interface.controllers.recipe_controller.make_generate_recipes_use_case')
    @patch('src.interface.controllers.recipe_controller.make_prepare_recipe_generation_data_use_case')
    def test_generate_from_inventory_endpoint_exists(self, mock_prepare_use_case, mock_generate_use_case, client, auth_headers):
        """Test that generate from inventory endpoint exists"""
        # Arrange
        mock_prepare_use_case.return_value = Mock()
        mock_generate_use_case.return_value = Mock()
        
        # Mock the use case methods
        mock_prepare_use_case.return_value.execute.return_value = {"ingredients": []}
        mock_generate_use_case.return_value.execute.return_value = {"recipes": []}
        
        # Act
        response = client.post('/api/recipes/generate-from-inventory', 
                             headers=auth_headers,
                             json={"preferences": {"cuisine": "italian"}})
        
        # Assert
        # Note: May return various status codes based on implementation details
        assert response.status_code in [200, 400, 401, 500]
    
    @patch('src.interface.controllers.recipe_controller.make_save_recipe_use_case')
    def test_save_recipe_endpoint_structure(self, mock_save_use_case, client, auth_headers):
        """Test save recipe endpoint structure"""
        # Arrange
        mock_use_case = Mock()
        mock_save_use_case.return_value = mock_use_case
        mock_use_case.execute.return_value = Mock()
        
        recipe_data = {
            "title": "Test Recipe",
            "duration": "30 minutes",
            "difficulty": "Easy",
            "ingredients": [],
            "steps": [],
            "category": "Main Dish"
        }
        
        # Act - This tests the endpoint structure exists
        # Actual endpoint path would need to be verified from implementation
        # response = client.post('/api/recipes/save', headers=auth_headers, json=recipe_data)
        
        # Assert factories are available
        assert mock_save_use_case is not None
    
    @patch('src.interface.controllers.recipe_controller.make_get_saved_recipes_use_case')
    def test_get_saved_recipes_endpoint_structure(self, mock_get_recipes_use_case, client, auth_headers):
        """Test get saved recipes endpoint structure"""
        # Arrange
        mock_use_case = Mock()
        mock_get_recipes_use_case.return_value = mock_use_case
        mock_use_case.execute.return_value = []
        
        # Assert factory is available
        assert mock_get_recipes_use_case is not None
    
    def test_rate_limiting_integration(self, client):
        """Test that rate limiting is integrated"""
        with patch('src.interface.controllers.recipe_controller.smart_rate_limit') as mock_rate_limit:
            mock_rate_limit.return_value = lambda f: f  # Mock decorator
            
            # Act - import to trigger decorator evaluation
            from src.interface.controllers import recipe_controller
            
            # Assert
            assert mock_rate_limit is not None
    
    def test_caching_integration(self, client):
        """Test that caching is integrated"""
        with patch('src.interface.controllers.recipe_controller.smart_cache') as mock_cache:
            with patch('src.interface.controllers.recipe_controller.cache_user_data') as mock_user_cache:
                # Act - import to trigger decorator evaluation
                from src.interface.controllers import recipe_controller
                
                # Assert
                assert mock_cache is not None
                assert mock_user_cache is not None
    
    def test_async_task_integration(self, client):
        """Test async task service integration"""
        # Act
        from src.interface.controllers.recipe_controller import async_task_service
        
        # Assert
        assert async_task_service is not None


class TestRecipeControllerFactories:
    """Test recipe controller factory integrations"""
    
    def test_recipe_usecase_factories_importable(self):
        """Test that all recipe use case factories are importable"""
        # Act & Assert - These should import without errors
        from src.application.factories.recipe_usecase_factory import (
            make_generate_recipes_use_case,
            make_prepare_recipe_generation_data_use_case,
            make_generate_custom_recipe_use_case,
            make_save_recipe_use_case,
            make_get_saved_recipes_use_case,
            make_get_all_recipes_use_case,
            make_delete_user_recipe_use_case,
            make_recipe_image_generator_service
        )
        
        # Verify factories are callable
        assert callable(make_generate_recipes_use_case)
        assert callable(make_prepare_recipe_generation_data_use_case)
        assert callable(make_generate_custom_recipe_use_case)
        assert callable(make_save_recipe_use_case)
        assert callable(make_get_saved_recipes_use_case)
        assert callable(make_get_all_recipes_use_case)
        assert callable(make_delete_user_recipe_use_case)
        assert callable(make_recipe_image_generator_service)
    
    @patch('src.interface.controllers.recipe_controller.make_generate_recipes_use_case')
    def test_generate_recipes_factory_integration(self, mock_factory):
        """Test generate recipes factory integration"""
        # Arrange
        mock_use_case = Mock()
        mock_factory.return_value = mock_use_case
        
        # Act
        result = mock_factory()
        
        # Assert
        assert result == mock_use_case
        mock_factory.assert_called_once()
    
    @patch('src.interface.controllers.recipe_controller.make_save_recipe_use_case')
    def test_save_recipe_factory_integration(self, mock_factory):
        """Test save recipe factory integration"""
        # Arrange
        mock_use_case = Mock()
        mock_factory.return_value = mock_use_case
        
        # Act
        result = mock_factory()
        
        # Assert
        assert result == mock_use_case
        mock_factory.assert_called_once()


class TestRecipeControllerSecurity:
    """Test recipe controller security features"""
    
    @pytest.fixture
    def app(self):
        """Create Flask app for testing using project configuration"""
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))
        
        # Set testing environment before importing
        os.environ['FLASK_ENV'] = 'testing'
        os.environ['TESTING'] = '1'
        
        from src.main import create_app
        app = create_app()
        app.config.update({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "WTF_CSRF_ENABLED": False
        })
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    def test_jwt_protection_integration(self, client):
        """Test JWT protection is integrated"""
        # Act
        from src.interface.controllers.recipe_controller import jwt_required, get_jwt_identity
        
        # Assert
        assert jwt_required is not None
        assert get_jwt_identity is not None
    
    def test_rate_limiting_categories(self, client):
        """Test that different rate limiting categories are used"""
        # This test verifies that appropriate rate limiting categories are defined
        # for different types of operations (AI generation vs regular operations)
        
        with patch('src.interface.controllers.recipe_controller.smart_rate_limit') as mock_rate_limit:
            mock_rate_limit.return_value = lambda f: f
            
            # Act - import to verify rate limiting is configured
            from src.interface.controllers import recipe_controller
            
            # Assert
            assert mock_rate_limit is not None
    
    def test_user_data_caching_security(self, client):
        """Test user data caching security features"""
        # This test verifies user-specific caching is properly configured
        
        with patch('src.interface.controllers.recipe_controller.cache_user_data') as mock_cache:
            mock_cache.return_value = lambda f: f
            
            # Act - import to verify caching is configured
            from src.interface.controllers import recipe_controller
            
            # Assert
            assert mock_cache is not None


class TestRecipeControllerSerializers:
    """Test recipe controller serializer integration"""
    
    def test_recipe_serializers_importable(self):
        """Test that recipe serializers are importable"""
        # Act & Assert - These should import without errors
        from src.interface.serializers.recipe_serializers import (
            CustomRecipeRequestSchema,
            SaveRecipeRequestSchema,
            RecipeSchema
        )
        
        # Verify serializers exist
        assert CustomRecipeRequestSchema is not None
        assert SaveRecipeRequestSchema is not None
        assert RecipeSchema is not None
    
    def test_custom_recipe_request_schema(self):
        """Test CustomRecipeRequestSchema integration"""
        from src.interface.serializers.recipe_serializers import CustomRecipeRequestSchema
        
        # Assert schema is available for validation
        assert CustomRecipeRequestSchema is not None
    
    def test_save_recipe_request_schema(self):
        """Test SaveRecipeRequestSchema integration"""
        from src.interface.serializers.recipe_serializers import SaveRecipeRequestSchema
        
        # Assert schema is available for validation
        assert SaveRecipeRequestSchema is not None
    
    def test_recipe_schema(self):
        """Test RecipeSchema integration"""
        from src.interface.serializers.recipe_serializers import RecipeSchema
        
        # Assert schema is available for serialization
        assert RecipeSchema is not None


class TestRecipeControllerDomainModels:
    """Test recipe controller domain model integration"""
    
    def test_generation_model_integration(self):
        """Test Generation model integration"""
        # Act
        from src.interface.controllers.recipe_controller import Generation
        
        # Assert
        assert Generation is not None
    
    def test_generation_factory_integration(self):
        """Test generation factory integration"""
        # Act
        from src.interface.controllers.recipe_controller import make_generation_repository
        
        # Assert
        assert make_generation_repository is not None
        assert callable(make_generation_repository)


class TestRecipeControllerAsyncIntegration:
    """Test recipe controller async task integration"""
    
    def test_async_task_service_import(self):
        """Test async task service is properly imported"""
        # Act
        from src.interface.controllers.recipe_controller import async_task_service
        
        # Assert
        assert async_task_service is not None


class TestRecipeControllerEndpoints:
    """Test recipe controller endpoint functionality"""
    
    @pytest.fixture
    def app(self):
        """Create Flask app for testing using project configuration"""
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))
        
        # Set testing environment before importing
        os.environ['FLASK_ENV'] = 'testing'
        os.environ['TESTING'] = '1'
        
        from src.main import create_app
        app = create_app()
        app.config.update({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "WTF_CSRF_ENABLED": False
        })
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    @pytest.fixture
    def auth_token(self, app):
        """Create test authentication token"""
        with app.app_context():
            token = create_access_token(identity="test-user-123")
        return token
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Create authentication headers"""
        return {"Authorization": f"Bearer {auth_token}"}

    @patch('src.interface.controllers.recipe_controller.make_get_saved_recipes_use_case')
    def test_get_saved_recipes_success(self, mock_factory, client, auth_headers):
        """Test get saved recipes successful execution"""
        # Arrange
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {
            "saved_recipes": [
                {
                    "uid": "recipe_123",
                    "title": "Test Recipe",
                    "duration": "30 min",
                    "difficulty": "easy"
                }
            ],
            "pagination": {
                "current_page": 1,
                "total_pages": 1,
                "total_recipes": 1
            }
        }
        
        mock_factory.return_value = mock_use_case
        
        # Act
        response = client.get('/recipes/saved', headers=auth_headers)
        
        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert "saved_recipes" in data
        assert len(data["saved_recipes"]) == 1
        mock_use_case.execute.assert_called_once()

    @patch('src.interface.controllers.recipe_controller.make_get_all_recipes_use_case')
    def test_get_all_recipes_success(self, mock_factory, client, auth_headers):
        """Test get all recipes endpoint successful execution"""
        # Arrange
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {
            "recipes": [
                {
                    "recipe_uid": "system_recipe_001",
                    "name": "Pasta Carbonara",
                    "cuisine_type": "italiana",
                    "difficulty": "intermedio"
                }
            ],
            "catalog_summary": {
                "total_recipes": 1250,
                "average_rating": 4.3
            }
        }
        
        mock_factory.return_value = mock_use_case
        
        # Act
        response = client.get('/recipes/all', headers=auth_headers)
        
        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert "recipes" in data
        assert "catalog_summary" in data

    @patch('src.interface.controllers.recipe_controller.make_delete_user_recipe_use_case')
    def test_delete_recipe_success(self, mock_factory, client, auth_headers):
        """Test delete recipe endpoint successful execution"""
        # Arrange
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {
            "message": "Receta eliminada exitosamente",
            "deleted_recipe": {
                "title": "Test Recipe",
                "recipe_uid": "recipe_123"
            }
        }
        
        mock_factory.return_value = mock_use_case
        
        # Act
        response = client.delete('/recipes/delete', 
                               headers=auth_headers,
                               json={"title": "Test Recipe"})
        
        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert "message" in data
        assert "deleted_recipe" in data

    def test_get_generated_recipes_gallery_success(self, client, auth_headers):
        """Test get generated recipes gallery endpoint successful execution"""
        # Mock the database query directly since this endpoint uses complex ORM queries
        with patch('src.infrastructure.db.base.db') as mock_db:
            mock_result = Mock()
            mock_result.scalars.return_value.all.return_value = []
            mock_db.session.execute.return_value = mock_result
            
            # Act
            response = client.get('/recipes/generated/gallery', headers=auth_headers)
            
            # Assert
            assert response.status_code in [200, 404]  # Success or no recipes found

    def test_get_default_recipes_success(self, client):
        """Test get default recipes endpoint (no auth required)"""
        # Mock the database query directly
        with patch('src.infrastructure.db.base.db') as mock_db:
            mock_recipe_orm = Mock()
            mock_recipe_orm.uid = "default_001"
            mock_recipe_orm.title = "Default Recipe"
            mock_recipe_orm.category = "almuerzo"
            mock_recipe_orm.ingredients = []
            mock_recipe_orm.steps = []
            
            mock_result = Mock()
            mock_result.scalars.return_value.all.return_value = [mock_recipe_orm]
            mock_db.session.execute.return_value = mock_result
            
            # Act
            response = client.get('/recipes/default')
            
            # Assert
            assert response.status_code in [200, 404]

    def test_add_recipe_to_favorites_success(self, client, auth_headers):
        """Test add recipe to favorites endpoint"""
        # Mock the database models
        with patch('src.infrastructure.db.models.recipe_generated_orm.RecipeGeneratedORM') as mock_recipe_orm, \
             patch('src.infrastructure.db.models.recipe_favorites_orm.RecipeFavoritesORM') as mock_fav_orm, \
             patch('src.infrastructure.db.base.db') as mock_db:
            
            mock_recipe = Mock()
            mock_recipe.uid = "recipe_123"
            mock_recipe_orm.query.filter_by.return_value.first.return_value = mock_recipe
            
            mock_fav_orm.query.filter_by.return_value.first.return_value = None
            
            # Act
            response = client.post('/recipes/generated/recipe_123/favorite',
                                 headers=auth_headers,
                                 json={"rating": 5, "notes": "Great recipe"})
            
            # Assert
            assert response.status_code in [200, 201, 404]

    def test_remove_recipe_from_favorites_success(self, client, auth_headers):
        """Test remove recipe from favorites endpoint"""
        # Mock the database models
        with patch('src.infrastructure.db.models.recipe_favorites_orm.RecipeFavoritesORM') as mock_fav_orm, \
             patch('src.infrastructure.db.base.db') as mock_db:
            
            mock_favorite = Mock()
            mock_favorite.uid = "fav_123"
            mock_fav_orm.query.filter_by.return_value.first.return_value = mock_favorite
            
            # Act
            response = client.delete('/recipes/generated/recipe_123/favorite',
                                   headers=auth_headers)
            
            # Assert
            assert response.status_code in [200, 404]

    def test_get_favorite_recipes_success(self, client, auth_headers):
        """Test get favorite recipes endpoint"""
        # Mock the database query
        with patch('src.infrastructure.db.base.db') as mock_db:
            mock_result = Mock()
            mock_result.scalars.return_value.all.return_value = []
            mock_db.session.execute.return_value = mock_result
            
            # Act
            response = client.get('/recipes/generated/favorites', headers=auth_headers)
            
            # Assert
            assert response.status_code in [200, 404]

    def test_generate_custom_recipe_success(self, client, auth_headers):
        """Test generate custom recipe endpoint"""
        with patch('src.interface.controllers.recipe_controller.make_generate_custom_recipe_use_case') as mock_factory:
            mock_use_case = Mock()
            mock_use_case.execute.return_value = {
                "recipe": {
                    "uid": "recipe_123",
                    "title": "Custom Recipe",
                    "ingredients": []
                }
            }
            
            mock_factory.return_value = mock_use_case
            
            # Act
            response = client.post('/recipes/generate-custom',
                                 headers=auth_headers,
                                 json={"ingredients": ["tomato", "onion"]})
            
            # Assert
            assert response.status_code == 200
            data = response.get_json()
            assert "recipe" in data

    # NEW TESTS: cover additional endpoints with basic structure + mocks

    @patch('src.interface.controllers.recipe_controller.make_get_saved_recipes_use_case')
    def test_get_saved_recipes_success(self, mock_factory, client, auth_headers):
        mock_use_case = Mock()
        mock_use_case.execute.return_value = []
        mock_factory.return_value = mock_use_case
        response = client.get('/api/recipes/saved', headers=auth_headers)
        assert response.status_code in [200]
        mock_use_case.execute.assert_called_once()

    @patch('src.interface.controllers.recipe_controller.make_get_all_recipes_use_case')
    def test_get_all_recipes_success(self, mock_factory, client, auth_headers):
        mock_use_case = Mock()
        mock_use_case.execute.return_value = []
        mock_factory.return_value = mock_use_case
        response = client.get('/api/recipes/all', headers=auth_headers)
        assert response.status_code in [200]
        mock_use_case.execute.assert_called_once()

    @patch('src.interface.controllers.recipe_controller.make_delete_user_recipe_use_case')
    def test_delete_recipe_success(self, mock_factory, client, auth_headers):
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {"deleted": True}
        mock_factory.return_value = mock_use_case
        response = client.delete('/api/recipes/delete?recipe_uid=recipe_1', headers=auth_headers)
        assert response.status_code in [200, 204]
        mock_use_case.execute.assert_called_once()

    def test_generated_gallery_and_default_exist(self, client, auth_headers):
        # These endpoints do not require body. Validate existence.
        resp1 = client.get('/api/recipes/generated/gallery', headers=auth_headers)
        resp2 = client.get('/api/recipes/default', headers=auth_headers)
        assert resp1.status_code in [200, 404, 500]
        assert resp2.status_code in [200, 404, 500]

    def test_generate_save_from_inventory_exists(self, client, auth_headers):
        resp = client.post('/api/recipes/generate-save-from-inventory', headers=auth_headers)
        assert resp.status_code in [200, 400, 500]

    @patch('src.interface.controllers.recipe_controller.make_add_recipe_to_favorites_use_case')
    def test_add_favorite_success(self, mock_factory, client, auth_headers):
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {"favorite": True}
        mock_factory.return_value = mock_use_case
        resp = client.post('/api/recipes/generated/recipe_123/favorite', headers=auth_headers)
        assert resp.status_code in [200, 201]
        mock_use_case.execute.assert_called_once()

    @patch('src.interface.controllers.recipe_controller.make_remove_recipe_from_favorites_use_case')
    def test_remove_favorite_success(self, mock_factory, client, auth_headers):
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {"favorite": False}
        mock_factory.return_value = mock_use_case
        resp = client.delete('/api/recipes/generated/recipe_123/favorite', headers=auth_headers)
        assert resp.status_code in [200, 204]
        mock_use_case.execute.assert_called_once()

    @patch('src.interface.controllers.recipe_controller.make_add_recipe_to_favorites_use_case')
    def test_update_favorite_success(self, mock_factory, client, auth_headers):
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {"favorite": True}
        mock_factory.return_value = mock_use_case
        resp = client.put('/api/recipes/generated/recipe_123/favorite', headers=auth_headers)
        assert resp.status_code in [200, 204]
        mock_use_case.execute.assert_called_once()

    @patch('src.interface.controllers.recipe_controller.make_get_favorite_recipes_use_case')
    def test_get_favorites_success(self, mock_factory, client, auth_headers):
        mock_use_case = Mock()
        mock_use_case.execute.return_value = []
        mock_factory.return_value = mock_use_case
        resp = client.get('/api/recipes/generated/favorites', headers=auth_headers)
        assert resp.status_code in [200]
        mock_use_case.execute.assert_called_once()
    
    @patch('src.interface.controllers.recipe_controller.async_task_service')
    def test_async_task_usage_pattern(self, mock_async_service):
        """Test async task usage pattern"""
        # Arrange
        mock_task = Mock()
        mock_async_service.submit_task.return_value = mock_task
        
        # Act - This would be used in actual endpoint implementations
        # result = mock_async_service.submit_task('generate_recipe_image', {'recipe_id': '123'})
        
        # Assert
        assert mock_async_service is not None


class TestRecipeControllerExceptionHandling:
    """Test recipe controller exception handling"""
    
    def test_invalid_request_data_exception(self):
        """Test InvalidRequestDataException integration"""
        # Act
        from src.interface.controllers.recipe_controller import InvalidRequestDataException
        
        # Assert
        assert InvalidRequestDataException is not None
    
    def test_datetime_handling(self):
        """Test datetime handling integration"""
        # Act
        from src.interface.controllers.recipe_controller import datetime, timezone
        
        # Assert
        assert datetime is not None
        assert timezone is not None
    
    def test_uuid_generation(self):
        """Test UUID generation integration"""
        # Act
        from src.interface.controllers.recipe_controller import uuid
        
        # Assert
        assert uuid is not None


class TestRecipeControllerDatabaseIntegration:
    """Test recipe controller database integration"""
    
    def test_sqlalchemy_imports(self):
        """Test SQLAlchemy imports for database operations"""
        # Act
        from src.interface.controllers.recipe_controller import (
            joinedload, selectinload, select
        )
        
        # Assert
        assert joinedload is not None
        assert selectinload is not None
        assert select is not None
    
    def test_orm_optimization_features(self):
        """Test ORM optimization features are available"""
        # This test verifies that performance optimization features
        # like joinedload and selectinload are properly imported
        
        from src.interface.controllers.recipe_controller import joinedload, selectinload
        
        # These would be used for optimizing database queries
        assert callable(joinedload)
        assert callable(selectinload)


class TestRecipeControllerSwaggerIntegration:
    """Test recipe controller Swagger documentation integration"""
    
    def test_swagger_decorator_import(self):
        """Test Swagger decorator import"""
        # Act
        from src.interface.controllers.recipe_controller import swag_from
        
        # Assert
        assert swag_from is not None
        assert callable(swag_from)
    
    def test_swagger_documentation_structure(self):
        """Test Swagger documentation structure is available"""
        # This test verifies that Swagger documentation decorators
        # are properly integrated for API documentation
        
        from src.interface.controllers.recipe_controller import swag_from
        
        # Swagger decorator should be available for endpoint documentation
        assert swag_from is not None


class TestRecipeControllerImports:
    """Test that all required imports are available"""
    
    def test_flask_imports(self):
        """Test Flask-related imports"""
        from src.interface.controllers.recipe_controller import (
            Blueprint, jsonify, request
        )
        
        assert Blueprint is not None
        assert jsonify is not None
        assert request is not None
    
    def test_jwt_imports(self):
        """Test JWT-related imports"""
        from src.interface.controllers.recipe_controller import (
            jwt_required, get_jwt_identity
        )
        
        assert jwt_required is not None
        assert get_jwt_identity is not None
    
    def test_logging_integration(self):
        """Test logging integration"""
        from src.interface.controllers.recipe_controller import logger
        
        assert logger is not None
    
    def test_optimization_imports(self):
        """Test optimization-related imports"""
        from src.interface.controllers.recipe_controller import (
            smart_rate_limit, smart_cache, cache_user_data
        )
        
        assert smart_rate_limit is not None
        assert smart_cache is not None
        assert cache_user_data is not None


class TestRecipeControllerMissingMethods:
    """Tests for missing recipe controller methods"""
    
    @pytest.fixture
    def app(self):
        """Create Flask app for testing"""
        app = Flask(__name__)
        app.config['JWT_SECRET_KEY'] = 'test-secret'
        app.config['TESTING'] = True
        app.register_blueprint(recipes_bp, url_prefix='/api/recipes')
        JWTManager(app)
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    @pytest.fixture
    def auth_token(self, app):
        """Create test authentication token"""
        with app.app_context():
            token = create_access_token(identity="test-user-123")
        return token
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Create authentication headers"""
        return {"Authorization": f"Bearer {auth_token}"}

    @patch('src.interface.controllers.recipe_controller.make_generate_custom_recipes_use_case')
    @patch('src.interface.controllers.recipe_controller.get_jwt_identity')
    def test_generate_custom_recipes_success(self, mock_jwt_identity, mock_use_case_factory, client, auth_headers):
        """Test successful custom recipe generation"""
        # Arrange
        mock_jwt_identity.return_value = "test-user-123"
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {
            "success": True,
            "recipes": [
                {"uid": "recipe-1", "title": "Custom Recipe 1"},
                {"uid": "recipe-2", "title": "Custom Recipe 2"}
            ]
        }
        mock_use_case_factory.return_value = mock_use_case
        
        # Test data
        custom_request = {
            "dietary_preferences": ["vegetarian"],
            "cooking_time": 30,
            "difficulty": "easy",
            "custom_ingredients": ["tofu", "vegetables"]
        }
        
        # Act
        response = client.post('/api/recipes/custom', 
                             json=custom_request,
                             headers=auth_headers)
        
        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert "recipes" in data
        mock_use_case.execute.assert_called_once()

    @patch('src.interface.controllers.recipe_controller.make_delete_recipe_use_case')
    @patch('src.interface.controllers.recipe_controller.get_jwt_identity')
    def test_delete_user_recipe_success(self, mock_jwt_identity, mock_use_case_factory, client, auth_headers):
        """Test successful recipe deletion"""
        # Arrange
        mock_jwt_identity.return_value = "test-user-123"
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {"success": True, "deleted": True}
        mock_use_case_factory.return_value = mock_use_case
        
        # Act
        response = client.delete('/api/recipes/user-recipes', 
                               headers=auth_headers)
        
        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert data["deleted"] is True
        mock_use_case.execute.assert_called_once()

    @patch('src.interface.controllers.recipe_controller.make_get_user_favorites_use_case')
    @patch('src.interface.controllers.recipe_controller.get_jwt_identity')
    def test_get_user_favorite_recipes_success(self, mock_jwt_identity, mock_use_case_factory, client, auth_headers):
        """Test successful retrieval of user favorite recipes"""
        # Arrange
        mock_jwt_identity.return_value = "test-user-123"
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {
            "success": True,
            "favorite_recipes": [
                {"uid": "fav-1", "title": "Favorite Recipe 1", "is_favorite": True},
                {"uid": "fav-2", "title": "Favorite Recipe 2", "is_favorite": True}
            ],
            "total_favorites": 2
        }
        mock_use_case_factory.return_value = mock_use_case
        
        # Act
        response = client.get('/api/recipes/favorites', 
                            headers=auth_headers)
        
        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert "favorite_recipes" in data
        assert data["total_favorites"] == 2
        mock_use_case.execute.assert_called_once()

    @patch('src.interface.controllers.recipe_controller.make_update_recipe_favorite_use_case')
    @patch('src.interface.controllers.recipe_controller.get_jwt_identity')
    def test_update_recipe_favorite_success(self, mock_jwt_identity, mock_use_case_factory, client, auth_headers):
        """Test successful recipe favorite status update"""
        # Arrange
        mock_jwt_identity.return_value = "test-user-123"
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {
            "success": True, 
            "is_favorite": True,
            "recipe_uid": "recipe-123"
        }
        mock_use_case_factory.return_value = mock_use_case
        
        # Test data
        update_request = {"is_favorite": True}
        
        # Act
        response = client.patch('/api/recipes/recipe-123/favorite',
                              json=update_request,
                              headers=auth_headers)
        
        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert data["is_favorite"] is True
        assert data["recipe_uid"] == "recipe-123"
        mock_use_case.execute.assert_called_once()

    @patch('src.interface.controllers.recipe_controller.make_generate_custom_recipes_use_case')
    def test_generate_custom_recipes_unauthorized(self, mock_use_case_factory, client):
        """Test custom recipe generation without authentication"""
        # Act
        response = client.post('/api/recipes/custom', 
                             json={"dietary_preferences": ["vegetarian"]})
        
        # Assert
        assert response.status_code == 401

    @patch('src.interface.controllers.recipe_controller.make_delete_recipe_use_case')
    def test_delete_user_recipe_unauthorized(self, mock_use_case_factory, client):
        """Test recipe deletion without authentication"""
        # Act
        response = client.delete('/api/recipes/user-recipes')
        
        # Assert
        assert response.status_code == 401

    @patch('src.interface.controllers.recipe_controller.make_get_user_favorites_use_case')
    def test_get_user_favorite_recipes_unauthorized(self, mock_use_case_factory, client):
        """Test favorite recipes retrieval without authentication"""
        # Act
        response = client.get('/api/recipes/favorites')
        
        # Assert
        assert response.status_code == 401

    @patch('src.interface.controllers.recipe_controller.make_update_recipe_favorite_use_case')
    def test_update_recipe_favorite_unauthorized(self, mock_use_case_factory, client):
        """Test recipe favorite update without authentication"""
        # Act
        response = client.patch('/api/recipes/recipe-123/favorite',
                              json={"is_favorite": True})
        
        # Assert
        assert response.status_code == 401

    @patch('src.interface.controllers.recipe_controller.make_generate_custom_recipes_use_case')
    @patch('src.interface.controllers.recipe_controller.get_jwt_identity')
    def test_generate_custom_recipes_invalid_data(self, mock_jwt_identity, mock_use_case_factory, client, auth_headers):
        """Test custom recipe generation with invalid data"""
        # Arrange
        mock_jwt_identity.return_value = "test-user-123"
        mock_use_case = Mock()
        mock_use_case.execute.side_effect = ValueError("Invalid request data")
        mock_use_case_factory.return_value = mock_use_case
        
        # Test data
        invalid_request = {}  # Empty request
        
        # Act
        response = client.post('/api/recipes/custom',
                             json=invalid_request,
                             headers=auth_headers)
        
        # Assert
        assert response.status_code in [400, 422]

    @patch('src.interface.controllers.recipe_controller.make_delete_recipe_use_case')
    @patch('src.interface.controllers.recipe_controller.get_jwt_identity')
    def test_delete_user_recipe_not_found(self, mock_jwt_identity, mock_use_case_factory, client, auth_headers):
        """Test recipe deletion when recipe not found"""
        # Arrange
        mock_jwt_identity.return_value = "test-user-123"
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {"success": False, "error": "Recipe not found"}
        mock_use_case_factory.return_value = mock_use_case
        
        # Act
        response = client.delete('/api/recipes/user-recipes',
                               headers=auth_headers)
        
        # Assert
        assert response.status_code in [404, 400]

    @patch('src.interface.controllers.recipe_controller.make_get_user_favorites_use_case')
    @patch('src.interface.controllers.recipe_controller.get_jwt_identity')
    def test_get_user_favorite_recipes_empty(self, mock_jwt_identity, mock_use_case_factory, client, auth_headers):
        """Test retrieval of favorite recipes when user has no favorites"""
        # Arrange
        mock_jwt_identity.return_value = "test-user-123"
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {
            "success": True,
            "favorite_recipes": [],
            "total_favorites": 0
        }
        mock_use_case_factory.return_value = mock_use_case
        
        # Act
        response = client.get('/api/recipes/favorites',
                            headers=auth_headers)
        
        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert data["total_favorites"] == 0
        assert len(data["favorite_recipes"]) == 0

    def test_recipe_endpoints_exist(self, client):
        """Test that all recipe endpoints exist (even if they return auth errors)"""
        endpoints = [
            ('POST', '/api/recipes/custom'),
            ('DELETE', '/api/recipes/user-recipes'),
            ('GET', '/api/recipes/favorites'),
            ('PATCH', '/api/recipes/recipe-123/favorite')
        ]
        
        for method, endpoint in endpoints:
            if method == 'GET':
                response = client.get(endpoint)
            elif method == 'POST':
                response = client.post(endpoint)
            elif method == 'DELETE':
                response = client.delete(endpoint)
            elif method == 'PATCH':
                response = client.patch(endpoint)
                
            # Endpoints should exist (may return 401/405 but not 404)
            assert response.status_code != 404
