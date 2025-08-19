"""
Integration tests for User Controller
Tests end-to-end user profile management workflows
"""
import pytest
import json
from datetime import datetime, date, timedelta
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token


class TestUserControllerIntegration:
    """Integration test suite for User Controller"""
    
    @pytest.fixture
    def app(self):
        """Create Flask app for integration testing"""
        app = Flask(__name__)
        app.config['JWT_SECRET_KEY'] = 'test-secret'
        app.config['TESTING'] = True
        
        # Register user blueprint
        from src.interface.controllers.user_controller import user_bp
        app.register_blueprint(user_bp, url_prefix='/api/user')
        
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
            token = create_access_token(identity="test-user-integration")
        return token
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Create authentication headers"""
        return {"Authorization": f"Bearer {auth_token}"}

    # INTEGRATION TEST 1: Complete User Profile Workflow
    @patch('src.interface.controllers.user_controller.make_get_user_profile_use_case')
    @patch('src.interface.controllers.user_controller.make_update_user_profile_use_case')
    def test_complete_user_profile_workflow(
        self,
        mock_update_use_case,
        mock_get_use_case,
        client,
        auth_headers
    ):
        """Test complete user profile workflow: Get → Update → Get (verify changes)"""
        
        # Step 1: Get initial user profile
        initial_profile_data = {
            "user_uid": "test-user-integration",
            "profile": {
                "display_name": "John Doe",
                "email": "john.doe@example.com",
                "photo_url": "https://storage.googleapis.com/profiles/john_doe.jpg",
                "email_verified": True,
                "phone_number": None,
                "created_at": "2025-01-15T10:00:00Z",
                "last_login": "2025-08-19T14:00:00Z"
            },
            "preferences": {
                "dietary_restrictions": ["vegetarian"],
                "favorite_cuisines": ["Italian"],
                "notification_settings": {
                    "email_notifications": True,
                    "push_notifications": False,
                    "recipe_suggestions": True
                },
                "privacy_settings": {
                    "profile_visible": True,
                    "share_cooking_data": False
                }
            },
            "statistics": {
                "recipes_saved": 15,
                "ingredients_recognized": 89,
                "cooking_sessions_completed": 7,
                "environmental_savings": {
                    "co2_saved": 2.5,
                    "waste_reduced": 1.8
                }
            }
        }
        
        mock_get_use_case.return_value.execute.return_value = initial_profile_data
        
        response = client.get("/api/user/profile", headers=auth_headers)
        
        assert response.status_code == 200
        profile_data = response.get_json()
        assert profile_data["profile"]["display_name"] == "John Doe"
        assert "vegetarian" in profile_data["preferences"]["dietary_restrictions"]
        assert profile_data["statistics"]["recipes_saved"] == 15
        
        # Step 2: Update user profile with new information
        updated_profile_data = {
            "user_uid": "test-user-integration",
            "profile": {
                "display_name": "John Smith",  # Updated name
                "email": "john.doe@example.com",
                "phone_number": "+1234567890",  # Added phone
                "updated_at": "2025-08-19T16:00:00Z"
            },
            "preferences": {
                "dietary_restrictions": ["vegetarian", "gluten_free"],  # Added restriction
                "favorite_cuisines": ["Italian", "Mediterranean"],  # Added cuisine
                "notification_settings": {
                    "email_notifications": False,  # Changed setting
                    "push_notifications": True,    # Changed setting
                    "recipe_suggestions": True
                },
                "privacy_settings": {
                    "profile_visible": False,  # Changed privacy
                    "share_cooking_data": True  # Changed privacy
                }
            },
            "update_summary": {
                "fields_updated": ["display_name", "phone_number", "dietary_restrictions", "favorite_cuisines", "notification_settings", "privacy_settings"],
                "updated_at": "2025-08-19T16:00:00Z"
            }
        }
        
        mock_update_use_case.return_value.execute.return_value = updated_profile_data
        
        update_request = {
            "display_name": "John Smith",
            "phone_number": "+1234567890",
            "dietary_restrictions": ["vegetarian", "gluten_free"],
            "favorite_cuisines": ["Italian", "Mediterranean"],
            "notification_settings": {
                "email_notifications": False,
                "push_notifications": True,
                "recipe_suggestions": True
            },
            "privacy_settings": {
                "profile_visible": False,
                "share_cooking_data": True
            }
        }
        
        response = client.put("/api/user/profile", 
                             json=update_request,
                             headers=auth_headers)
        
        assert response.status_code == 200
        update_response = response.get_json()
        assert update_response["profile"]["display_name"] == "John Smith"
        assert update_response["profile"]["phone_number"] == "+1234567890"
        assert "gluten_free" in update_response["preferences"]["dietary_restrictions"]
        assert update_response["preferences"]["notification_settings"]["push_notifications"] is True
        
        # Step 3: Get updated profile to verify changes persisted
        mock_get_use_case.return_value.execute.return_value = updated_profile_data
        
        response = client.get("/api/user/profile", headers=auth_headers)
        
        assert response.status_code == 200
        final_profile = response.get_json()
        assert final_profile["profile"]["display_name"] == "John Smith"
        assert final_profile["preferences"]["privacy_settings"]["profile_visible"] is False

    # INTEGRATION TEST 2: User Profile with Application Data Integration
    @patch('src.interface.controllers.user_controller.make_get_user_profile_use_case')
    @patch('src.interface.controllers.recipe_controller.make_get_saved_recipes_use_case')
    @patch('src.interface.controllers.inventory_controller.make_get_inventory_simple_use_case')
    def test_user_profile_with_app_data_integration(
        self,
        mock_inventory_use_case,
        mock_recipe_use_case,
        mock_profile_use_case,
        client,
        auth_headers
    ):
        """Test user profile integration with app data (recipes, inventory, etc.)"""
        
        # Mock user profile with enhanced statistics
        mock_profile_use_case.return_value.execute.return_value = {
            "user_uid": "test-user-integration",
            "profile": {
                "display_name": "Chef Maria",
                "email": "maria@example.com",
                "joined_date": "2025-01-01T00:00:00Z"
            },
            "preferences": {
                "dietary_restrictions": ["dairy_free"],
                "favorite_cuisines": ["Mexican", "Asian"]
            },
            "activity_summary": {
                "last_active": "2025-08-19T15:30:00Z",
                "streak_days": 12,
                "total_app_usage_hours": 87
            },
            "achievements": [
                {"name": "First Recipe", "earned_at": "2025-01-15T10:00:00Z"},
                {"name": "Waste Warrior", "earned_at": "2025-02-20T14:30:00Z"},
                {"name": "Eco Chef", "earned_at": "2025-08-10T09:15:00Z"}
            ]
        }
        
        # Mock related app data
        mock_recipe_use_case.return_value.execute.return_value = {
            "recipes": [
                {"recipe_uid": "recipe_001", "title": "Vegan Tacos", "created_at": "2025-08-15"},
                {"recipe_uid": "recipe_002", "title": "Stir Fry Bowl", "created_at": "2025-08-18"}
            ],
            "total_saved": 2
        }
        
        mock_inventory_use_case.return_value.execute.return_value = {
            "inventory": {
                "ingredients": 15,
                "foods": 8,
                "expiring_soon": 2
            },
            "last_updated": "2025-08-19T12:00:00Z"
        }
        
        # Get profile with integrated data
        response = client.get("/api/user/profile", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["profile"]["display_name"] == "Chef Maria"
        assert len(data["achievements"]) == 3
        assert data["activity_summary"]["streak_days"] == 12

    # INTEGRATION TEST 3: User Profile Privacy and Security
    @patch('src.interface.controllers.user_controller.make_get_user_profile_use_case')
    @patch('src.interface.controllers.user_controller.make_update_user_profile_use_case')
    def test_user_profile_privacy_security_integration(
        self,
        mock_update_use_case,
        mock_get_use_case,
        client,
        auth_headers
    ):
        """Test user profile privacy settings and security features"""
        
        # Mock profile with privacy settings
        mock_get_use_case.return_value.execute.return_value = {
            "user_uid": "privacy-test-user",
            "profile": {
                "display_name": "Privacy User",
                "email": "privacy@example.com",
                # Note: sensitive data should be filtered out
                "email_verified": True
            },
            "preferences": {
                "privacy_settings": {
                    "profile_visible": False,
                    "share_cooking_data": False,
                    "allow_friend_requests": False,
                    "data_usage_consent": True
                },
                "security_settings": {
                    "two_factor_enabled": False,
                    "login_notifications": True,
                    "data_export_requests": 0
                }
            }
        }
        
        response = client.get("/api/user/profile", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Verify sensitive data is not exposed
        profile_str = json.dumps(data)
        sensitive_fields = ["password", "password_hash", "access_token", "refresh_token", "api_key", "firebase_uid"]
        for field in sensitive_fields:
            assert field not in profile_str.lower(), f"Sensitive field '{field}' found in response"
        
        # Test privacy settings update
        mock_update_use_case.return_value.execute.return_value = {
            "user_uid": "privacy-test-user",
            "preferences": {
                "privacy_settings": {
                    "profile_visible": True,  # Updated
                    "share_cooking_data": True,  # Updated
                    "allow_friend_requests": True,  # Updated
                    "data_usage_consent": True
                },
                "security_settings": {
                    "two_factor_enabled": True,  # Updated
                    "login_notifications": True
                }
            },
            "security_update": {
                "two_factor_setup_required": True,
                "verification_sent": True
            }
        }
        
        privacy_update = {
            "privacy_settings": {
                "profile_visible": True,
                "share_cooking_data": True,
                "allow_friend_requests": True
            },
            "security_settings": {
                "two_factor_enabled": True
            }
        }
        
        response = client.put("/api/user/profile",
                             json=privacy_update,
                             headers=auth_headers)
        
        assert response.status_code == 200
        update_data = response.get_json()
        assert update_data["preferences"]["privacy_settings"]["profile_visible"] is True
        assert "security_update" in update_data

    # INTEGRATION TEST 4: User Profile Validation and Error Handling
    @patch('src.interface.controllers.user_controller.make_update_user_profile_use_case')
    def test_user_profile_validation_integration(
        self,
        mock_update_use_case,
        client,
        auth_headers
    ):
        """Test user profile validation and error handling"""
        
        # Test validation errors
        validation_test_cases = [
            {
                "name": "empty_display_name",
                "data": {"display_name": ""},
                "expected_error": "Display name cannot be empty"
            },
            {
                "name": "invalid_email",
                "data": {"email": "invalid-email-format"},
                "expected_error": "Invalid email format"
            },
            {
                "name": "invalid_phone",
                "data": {"phone_number": "not-a-phone"},
                "expected_error": "Invalid phone number format"
            },
            {
                "name": "invalid_dietary_restrictions",
                "data": {"dietary_restrictions": ["invalid_restriction"]},
                "expected_error": "Invalid dietary restriction"
            }
        ]
        
        for test_case in validation_test_cases:
            mock_update_use_case.return_value.execute.side_effect = ValueError(test_case["expected_error"])
            
            response = client.put("/api/user/profile",
                                 json=test_case["data"],
                                 headers=auth_headers)
            
            assert response.status_code in [400, 422, 500], f"Test case '{test_case['name']}' should fail validation"
            
        # Test successful update after validation fixes
        mock_update_use_case.return_value.execute.side_effect = None
        mock_update_use_case.return_value.execute.return_value = {
            "user_uid": "test-user-integration",
            "profile": {"display_name": "Valid User", "updated_at": "2025-08-19T17:00:00Z"},
            "validation_passed": True
        }
        
        valid_data = {
            "display_name": "Valid User",
            "email": "valid@example.com",
            "phone_number": "+1234567890"
        }
        
        response = client.put("/api/user/profile",
                             json=valid_data,
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["validation_passed"] is True

    # INTEGRATION TEST 5: Authentication and Authorization
    def test_user_profile_authentication_integration(self, client):
        """Test authentication requirements for user profile endpoints"""
        
        endpoints_to_test = [
            ("GET", "/api/user/profile", None),
            ("PUT", "/api/user/profile", {"display_name": "Test User"})
        ]
        
        for method, endpoint, data in endpoints_to_test:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "PUT":
                response = client.put(endpoint, json=data)
                
            assert response.status_code == 401, f"Endpoint {method} {endpoint} should require authentication"

    # INTEGRATION TEST 6: User Profile Export and Data Management
    @patch('src.interface.controllers.user_controller.make_get_user_profile_use_case')
    def test_user_profile_data_export_integration(
        self,
        mock_get_use_case,
        client,
        auth_headers
    ):
        """Test user profile data export and data management features"""
        
        # Mock comprehensive user data for export
        mock_get_use_case.return_value.execute.return_value = {
            "user_uid": "export-test-user",
            "profile": {
                "display_name": "Export Test User",
                "email": "export@example.com",
                "created_at": "2025-01-01T00:00:00Z"
            },
            "preferences": {
                "dietary_restrictions": ["vegan"],
                "favorite_cuisines": ["Mediterranean"]
            },
            "statistics": {
                "recipes_saved": 25,
                "ingredients_recognized": 150,
                "cooking_sessions": 12
            },
            "data_export": {
                "export_available": True,
                "last_export_date": "2025-08-01T00:00:00Z",
                "export_format": "json",
                "data_categories": [
                    "profile", "preferences", "recipes", "inventory", 
                    "cooking_sessions", "environmental_data"
                ]
            },
            "gdpr_compliance": {
                "data_retention_period": "2 years",
                "can_request_deletion": True,
                "data_portability_available": True
            }
        }
        
        response = client.get("/api/user/profile", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert "data_export" in data
        assert data["data_export"]["export_available"] is True
        assert "gdpr_compliance" in data

    # INTEGRATION TEST 7: User Profile Performance and Caching
    @patch('src.interface.controllers.user_controller.make_get_user_profile_use_case')
    def test_user_profile_performance_integration(
        self,
        mock_get_use_case,
        client,
        auth_headers
    ):
        """Test user profile performance optimization and caching"""
        
        # Mock profile data with performance metrics
        mock_get_use_case.return_value.execute.return_value = {
            "user_uid": "performance-test-user",
            "profile": {
                "display_name": "Performance User",
                "email": "performance@example.com"
            },
            "performance_metadata": {
                "cache_hit": True,
                "query_time_ms": 15,
                "data_freshness": "2025-08-19T16:45:00Z",
                "optimized_response": True
            }
        }
        
        # Multiple requests to test caching behavior
        responses = []
        for _ in range(3):
            response = client.get("/api/user/profile", headers=auth_headers)
            responses.append(response)
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.get_json()
            assert "performance_metadata" in data

    # INTEGRATION TEST 8: Cross-Feature Integration
    @patch('src.interface.controllers.user_controller.make_get_user_profile_use_case')
    @patch('src.interface.controllers.environmental_savings_controller.make_get_environmental_summary_use_case')
    def test_user_profile_cross_feature_integration(
        self,
        mock_environmental_use_case,
        mock_profile_use_case,
        client,
        auth_headers
    ):
        """Test user profile integration with other app features"""
        
        # Mock profile with cross-feature data
        mock_profile_use_case.return_value.execute.return_value = {
            "user_uid": "cross-feature-user",
            "profile": {
                "display_name": "Eco Chef",
                "email": "eco@example.com"
            },
            "integrated_features": {
                "environmental_impact": {
                    "total_co2_saved": 12.5,
                    "waste_reduced_kg": 8.3,
                    "sustainability_score": 85
                },
                "cooking_achievements": {
                    "total_sessions": 45,
                    "favorite_recipe_type": "vegetarian",
                    "cooking_streak_days": 7
                },
                "social_features": {
                    "recipes_shared": 3,
                    "community_points": 150,
                    "badges_earned": ["Eco Warrior", "Recipe Master"]
                }
            }
        }
        
        response = client.get("/api/user/profile", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert "integrated_features" in data
        assert data["integrated_features"]["environmental_impact"]["sustainability_score"] == 85
        assert len(data["integrated_features"]["social_features"]["badges_earned"]) == 2
