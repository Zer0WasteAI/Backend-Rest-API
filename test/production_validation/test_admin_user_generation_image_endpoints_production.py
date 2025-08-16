"""
Production Validation Tests for Admin, User, Generation, and Image Management Endpoints
Tests remaining endpoints for complete production readiness validation
"""
import pytest
import json
import io
import time
from unittest.mock import patch, MagicMock
from werkzeug.datastructures import FileStorage
from src.main import create_app


class TestRemainingEndpointsProduction:
    """Production validation tests for Admin, User, Generation, and Image Management endpoints"""

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

    @pytest.fixture
    def internal_headers(self):
        return {"X-Internal-Secret": "test-internal-secret"}

    # ================================================================
    # ADMIN CONTROLLER TESTS - /api/admin/
    # ================================================================

    def test_admin_cleanup_tokens_success(self, client, internal_headers):
        """Test admin token cleanup endpoint"""
        with patch('src.application.use_cases.admin.cleanup_expired_tokens_use_case.CleanupExpiredTokensUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "message": "Token cleanup completed successfully",
                "tokens_cleaned": {
                    "expired_access_tokens": 15,
                    "expired_refresh_tokens": 8,
                    "blacklisted_tokens": 3
                },
                "total_cleaned": 26,
                "cleanup_duration": "2.3 seconds",
                "next_cleanup_scheduled": "2024-01-11T10:00:00Z"
            }

            response = client.post('/api/admin/cleanup-tokens',
                headers=internal_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['total_cleaned'] == 26
            assert 'tokens_cleaned' in data
            assert data['tokens_cleaned']['expired_access_tokens'] == 15

    def test_admin_cleanup_tokens_unauthorized(self, client, auth_headers):
        """Test admin cleanup without internal secret"""
        response = client.post('/api/admin/cleanup-tokens',
            headers=auth_headers)  # Regular user token, not internal secret

        assert response.status_code == 401

    def test_admin_cleanup_tokens_missing_header(self, client):
        """Test admin cleanup without any authentication"""
        response = client.post('/api/admin/cleanup-tokens')

        assert response.status_code == 401

    def test_admin_security_stats_success(self, client, internal_headers):
        """Test admin security statistics endpoint"""
        with patch('src.application.use_cases.admin.get_security_stats_use_case.GetSecurityStatsUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "security_statistics": {
                    "authentication": {
                        "total_login_attempts_24h": 1250,
                        "successful_logins_24h": 1180,
                        "failed_login_attempts_24h": 70,
                        "suspicious_activity_count": 5
                    },
                    "tokens": {
                        "active_access_tokens": 890,
                        "active_refresh_tokens": 445,
                        "blacklisted_tokens": 23,
                        "expired_tokens_pending_cleanup": 12
                    },
                    "rate_limiting": {
                        "rate_limited_requests_24h": 45,
                        "most_limited_endpoints": [
                            {"endpoint": "/api/auth/signin", "blocks": 20},
                            {"endpoint": "/api/recognition/ingredients", "blocks": 15}
                        ]
                    },
                    "security_events": {
                        "sql_injection_attempts": 3,
                        "xss_attempts": 2,
                        "suspicious_file_uploads": 1
                    }
                },
                "system_health": {
                    "database_status": "healthy",
                    "redis_status": "healthy",
                    "external_services_status": "operational"
                },
                "generated_at": "2024-01-10T10:00:00Z"
            }

            response = client.get('/api/admin/security-stats',
                headers=internal_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert 'security_statistics' in data
            assert data['security_statistics']['authentication']['total_login_attempts_24h'] == 1250
            assert 'system_health' in data

    def test_admin_security_stats_unauthorized(self, client):
        """Test admin security stats without internal secret"""
        response = client.get('/api/admin/security-stats')

        assert response.status_code == 401

    # ================================================================
    # USER CONTROLLER TESTS - /api/user/
    # ================================================================

    def test_user_get_profile_success(self, client, auth_headers):
        """Test getting user profile from Firestore"""
        with patch('src.application.use_cases.user.get_user_profile_use_case.GetUserProfileUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "user_profile": {
                    "uid": "test-user-uid",
                    "email": "test@example.com",
                    "display_name": "Test User",
                    "profile_picture": "https://example.com/avatar.jpg",
                    "preferences": {
                        "dietary_restrictions": ["vegetarian"],
                        "cuisine_preferences": ["italian", "mexican"],
                        "cooking_skill_level": "intermediate"
                    },
                    "statistics": {
                        "recipes_generated": 25,
                        "meal_plans_created": 12,
                        "environmental_savings_total": 15.7
                    },
                    "account_settings": {
                        "notifications_enabled": True,
                        "public_profile": False,
                        "preferred_units": "metric"
                    }
                },
                "last_updated": "2024-01-10T10:00:00Z",
                "profile_completeness": 85
            }

            response = client.get('/api/user/profile',
                headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['user_profile']['uid'] == "test-user-uid"
            assert data['user_profile']['email'] == "test@example.com"
            assert data['profile_completeness'] == 85
            assert 'statistics' in data['user_profile']

    def test_user_get_profile_unauthorized(self, client):
        """Test getting profile without authentication"""
        response = client.get('/api/user/profile')

        assert response.status_code == 401

    def test_user_get_profile_not_found(self, client, auth_headers):
        """Test getting profile when user profile doesn't exist"""
        with patch('src.application.use_cases.user.get_user_profile_use_case.GetUserProfileUseCase.execute') as mock_execute:
            mock_execute.side_effect = Exception("User profile not found")

            response = client.get('/api/user/profile',
                headers=auth_headers)

            assert response.status_code == 404

    def test_user_update_profile_success(self, client, auth_headers):
        """Test updating user profile"""
        with patch('src.application.use_cases.user.update_user_profile_use_case.UpdateUserProfileUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "message": "Profile updated successfully",
                "updated_fields": ["display_name", "preferences.dietary_restrictions"],
                "user_profile": {
                    "uid": "test-user-uid",
                    "display_name": "Updated User",
                    "preferences": {
                        "dietary_restrictions": ["vegan"],
                        "cuisine_preferences": ["asian", "mediterranean"]
                    }
                },
                "profile_completeness": 90,
                "updated_at": "2024-01-10T15:30:00Z"
            }

            profile_updates = {
                "display_name": "Updated User",
                "preferences": {
                    "dietary_restrictions": ["vegan"],
                    "cuisine_preferences": ["asian", "mediterranean"]
                },
                "account_settings": {
                    "notifications_enabled": False
                }
            }

            response = client.put('/api/user/profile',
                json=profile_updates,
                headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['user_profile']['display_name'] == "Updated User"
            assert "display_name" in data['updated_fields']
            assert data['profile_completeness'] == 90

    def test_user_update_profile_invalid_data(self, client, auth_headers):
        """Test updating profile with invalid data"""
        invalid_updates = {
            "email": "invalid-email",  # Should not be updateable directly
            "uid": "hacker-uid",       # Should not be updateable
            "preferences": {
                "dietary_restrictions": ["invalid_restriction"]
            }
        }

        response = client.put('/api/user/profile',
            json=invalid_updates,
            headers=auth_headers)

        assert response.status_code == 400

    def test_user_update_profile_unauthorized(self, client):
        """Test updating profile without authentication"""
        response = client.put('/api/user/profile',
            json={"display_name": "Test"})

        assert response.status_code == 401

    # ================================================================
    # GENERATION CONTROLLER TESTS - /api/generation/
    # ================================================================

    def test_generation_image_status_success(self, client, auth_headers):
        """Test checking image generation task status"""
        with patch('src.application.use_cases.generation.get_generation_status_use_case.GetGenerationStatusUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "task_id": "img_gen_task_123",
                "status": "in_progress",
                "progress": {
                    "current_step": "generating_images",
                    "completed_images": 3,
                    "total_images": 5,
                    "percentage": 60
                },
                "estimated_completion": "2024-01-10T10:05:00Z",
                "generated_images": [
                    {
                        "recipe_uid": "recipe_1",
                        "image_url": "https://storage.example.com/recipe_1.jpg",
                        "generation_time": "3.2s"
                    },
                    {
                        "recipe_uid": "recipe_2", 
                        "image_url": "https://storage.example.com/recipe_2.jpg",
                        "generation_time": "2.8s"
                    }
                ]
            }

            response = client.get('/api/generation/images/status/img_gen_task_123',
                headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['task_id'] == "img_gen_task_123"
            assert data['status'] == "in_progress"
            assert data['progress']['percentage'] == 60
            assert len(data['generated_images']) == 2

    def test_generation_image_status_completed(self, client, auth_headers):
        """Test checking completed image generation status"""
        with patch('src.application.use_cases.generation.get_generation_status_use_case.GetGenerationStatusUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "task_id": "img_gen_task_456",
                "status": "completed",
                "progress": {
                    "percentage": 100,
                    "completed_images": 4,
                    "total_images": 4
                },
                "completion_time": "2024-01-10T10:08:00Z",
                "total_generation_time": "12.5s",
                "generated_images": [
                    {"recipe_uid": f"recipe_{i}", "image_url": f"https://storage.example.com/recipe_{i}.jpg"}
                    for i in range(1, 5)
                ]
            }

            response = client.get('/api/generation/images/status/img_gen_task_456',
                headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == "completed"
            assert data['progress']['percentage'] == 100
            assert len(data['generated_images']) == 4

    def test_generation_image_status_not_found(self, client, auth_headers):
        """Test checking status of non-existent task"""
        with patch('src.application.use_cases.generation.get_generation_status_use_case.GetGenerationStatusUseCase.execute') as mock_execute:
            mock_execute.side_effect = Exception("Task not found")

            response = client.get('/api/generation/images/status/nonexistent_task',
                headers=auth_headers)

            assert response.status_code == 404

    def test_generation_get_images_success(self, client, auth_headers):
        """Test getting generated recipes with updated images"""
        with patch('src.application.use_cases.generation.get_generated_recipes_with_images_use_case.GetGeneratedRecipesWithImagesUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "generation_id": "gen_123",
                "recipes_with_images": [
                    {
                        "recipe_uid": "recipe_1",
                        "title": "Vegetable Pasta",
                        "image_url": "https://storage.example.com/pasta.jpg",
                        "image_status": "generated",
                        "generated_at": "2024-01-10T10:00:00Z"
                    },
                    {
                        "recipe_uid": "recipe_2",
                        "title": "Quinoa Salad",
                        "image_url": "https://storage.example.com/salad.jpg", 
                        "image_status": "generated",
                        "generated_at": "2024-01-10T10:02:00Z"
                    }
                ],
                "total_recipes": 2,
                "all_images_ready": True,
                "generation_metadata": {
                    "started_at": "2024-01-10T09:55:00Z",
                    "completed_at": "2024-01-10T10:02:00Z",
                    "total_generation_time": "7 minutes"
                }
            }

            response = client.get('/api/generation/gen_123/images',
                headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['generation_id'] == "gen_123"
            assert data['total_recipes'] == 2
            assert data['all_images_ready'] == True
            assert len(data['recipes_with_images']) == 2

    def test_generation_get_images_invalid_id(self, client, auth_headers):
        """Test getting images with invalid generation ID"""
        with patch('src.application.use_cases.generation.get_generated_recipes_with_images_use_case.GetGeneratedRecipesWithImagesUseCase.execute') as mock_execute:
            mock_execute.side_effect = Exception("Generation not found")

            response = client.get('/api/generation/invalid_gen_id/images',
                headers=auth_headers)

            assert response.status_code == 404

    def test_generation_unauthorized_access(self, client):
        """Test generation endpoints without authentication"""
        endpoints = [
            '/api/generation/images/status/task_123',
            '/api/generation/gen_123/images'
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401

    # ================================================================
    # IMAGE MANAGEMENT CONTROLLER TESTS - /api/image_management/
    # ================================================================

    def test_image_assign_success(self, client, auth_headers):
        """Test assigning reference image to ingredient"""
        with patch('src.application.use_cases.image_management.assign_image_reference_use_case.AssignImageReferenceUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "message": "Image assigned successfully",
                "assignment": {
                    "ingredient_name": "tomato",
                    "image_url": "https://storage.example.com/tomato_ref.jpg",
                    "image_id": "img_ref_123",
                    "confidence_score": 0.95
                },
                "previous_image": {
                    "image_url": "https://storage.example.com/old_tomato.jpg",
                    "replaced": True
                },
                "assigned_at": "2024-01-10T10:00:00Z"
            }

            assignment_data = {
                "ingredient_name": "tomato",
                "image_url": "https://storage.example.com/tomato_ref.jpg",
                "replace_existing": True
            }

            response = client.post('/api/image_management/assign_image',
                json=assignment_data,
                headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['assignment']['ingredient_name'] == "tomato"
            assert data['previous_image']['replaced'] == True

    def test_image_assign_invalid_ingredient(self, client, auth_headers):
        """Test assigning image to invalid ingredient"""
        assignment_data = {
            "ingredient_name": "",  # Empty ingredient name
            "image_url": "https://storage.example.com/image.jpg"
        }

        response = client.post('/api/image_management/assign_image',
            json=assignment_data,
            headers=auth_headers)

        assert response.status_code == 400

    def test_image_assign_invalid_url(self, client, auth_headers):
        """Test assigning invalid image URL"""
        assignment_data = {
            "ingredient_name": "tomato",
            "image_url": "not-a-valid-url"
        }

        response = client.post('/api/image_management/assign_image',
            json=assignment_data,
            headers=auth_headers)

        assert response.status_code == 400

    def test_image_search_similar_success(self, client, auth_headers):
        """Test searching for similar images"""
        with patch('src.application.use_cases.image_management.search_similar_images_use_case.SearchSimilarImagesUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "query_ingredient": "tomato",
                "similar_images": [
                    {
                        "image_url": "https://storage.example.com/tomato_1.jpg",
                        "similarity_score": 0.92,
                        "ingredient": "tomato",
                        "image_id": "img_1"
                    },
                    {
                        "image_url": "https://storage.example.com/cherry_tomato.jpg",
                        "similarity_score": 0.87,
                        "ingredient": "cherry tomato",
                        "image_id": "img_2"
                    }
                ],
                "total_similar_images": 2,
                "search_time": "0.8s"
            }

            search_data = {
                "ingredient_name": "tomato",
                "similarity_threshold": 0.8,
                "max_results": 10
            }

            response = client.post('/api/image_management/search_similar_images',
                json=search_data,
                headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['query_ingredient'] == "tomato"
            assert data['total_similar_images'] == 2
            assert len(data['similar_images']) == 2

    def test_image_search_no_results(self, client, auth_headers):
        """Test searching with no similar images found"""
        with patch('src.application.use_cases.image_management.search_similar_images_use_case.SearchSimilarImagesUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "query_ingredient": "exotic_fruit",
                "similar_images": [],
                "total_similar_images": 0,
                "message": "No similar images found"
            }

            search_data = {
                "ingredient_name": "exotic_fruit",
                "similarity_threshold": 0.9
            }

            response = client.post('/api/image_management/search_similar_images',
                json=search_data,
                headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['total_similar_images'] == 0
            assert data['similar_images'] == []

    def test_image_sync_success(self, client, internal_headers):
        """Test syncing images with database (internal endpoint)"""
        with patch('src.application.use_cases.image_management.sync_image_loader_use_case.SyncImageLoaderUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "sync_summary": {
                    "images_processed": 150,
                    "new_images_added": 25,
                    "updated_images": 8,
                    "removed_images": 3,
                    "duplicate_images_found": 2
                },
                "sync_duration": "45.2s",
                "errors_encountered": [],
                "next_sync_recommended": "2024-01-11T10:00:00Z"
            }

            response = client.post('/api/image_management/sync_images',
                headers=internal_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['sync_summary']['images_processed'] == 150
            assert data['sync_summary']['new_images_added'] == 25
            assert len(data['errors_encountered']) == 0

    def test_image_sync_unauthorized(self, client, auth_headers):
        """Test image sync without internal secret"""
        response = client.post('/api/image_management/sync_images',
            headers=auth_headers)

        assert response.status_code == 401

    def test_image_upload_success(self, client, auth_headers):
        """Test image file upload"""
        with patch('src.application.use_cases.image_management.upload_image_use_case.UploadImageUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "message": "Image uploaded successfully",
                "uploaded_image": {
                    "image_id": "uploaded_img_123",
                    "image_url": "https://storage.example.com/uploaded_image.jpg",
                    "file_name": "test_image.jpg",
                    "file_size": "256KB",
                    "image_dimensions": "800x600"
                },
                "upload_time": "2.1s",
                "processing_applied": ["resize", "compress", "format_optimization"]
            }

            # Create mock file
            data = {
                'image': (io.BytesIO(b'fake image data'), 'test_image.jpg'),
                'category': 'ingredient',
                'description': 'Test ingredient image'
            }

            response = client.post('/api/image_management/upload_image',
                data=data,
                headers=auth_headers,
                content_type='multipart/form-data')

            assert response.status_code == 201
            data = response.get_json()
            assert 'uploaded_image' in data
            assert data['uploaded_image']['file_name'] == "test_image.jpg"

    def test_image_upload_invalid_file(self, client, auth_headers):
        """Test uploading invalid image file"""
        # Test various invalid files
        invalid_files = [
            ('document.pdf', b'fake pdf data', 'application/pdf'),
            ('script.js', b'alert("xss")', 'text/javascript'),
            ('large_file.jpg', b'x' * (11 * 1024 * 1024), 'image/jpeg'),  # 11MB
        ]

        for filename, content, content_type in invalid_files:
            data = {
                'image': (io.BytesIO(content), filename)
            }

            response = client.post('/api/image_management/upload_image',
                data=data,
                headers=auth_headers,
                content_type='multipart/form-data')

            assert response.status_code == 400

    def test_image_upload_missing_file(self, client, auth_headers):
        """Test upload without file"""
        response = client.post('/api/image_management/upload_image',
            data={},
            headers=auth_headers,
            content_type='multipart/form-data')

        assert response.status_code == 400

    # ================================================================
    # Cross-Controller Security and Performance Tests
    # ================================================================

    def test_all_endpoints_security_headers(self, client, auth_headers, internal_headers):
        """Test that all endpoints have proper security headers"""
        test_endpoints = [
            ('GET', '/api/user/profile', auth_headers),
            ('GET', '/api/admin/security-stats', internal_headers),
            ('GET', '/api/generation/images/status/test_task', auth_headers)
        ]

        for method, endpoint, headers in test_endpoints:
            response = getattr(client, method.lower())(endpoint, headers=headers)
            
            # Check for security headers
            assert 'X-Content-Type-Options' in response.headers
            assert 'X-Frame-Options' in response.headers

    def test_all_endpoints_rate_limiting(self, client, auth_headers):
        """Test rate limiting across different endpoint categories"""
        # Test data_read category (100 req/min)
        with patch('src.application.use_cases.user.get_user_profile_use_case.GetUserProfileUseCase.execute'):
            for i in range(102):
                response = client.get('/api/user/profile', headers=auth_headers)
                
                if i < 100:
                    assert response.status_code in [200, 404]
                else:
                    assert response.status_code == 429

    def test_concurrent_requests_across_controllers(self, client, auth_headers):
        """Test concurrent requests across different controllers"""
        import threading
        results = []
        
        def make_requests():
            endpoints = [
                '/api/user/profile',
                '/api/generation/images/status/test_task'
            ]
            
            for endpoint in endpoints:
                response = client.get(endpoint, headers=auth_headers)
                results.append(response.status_code)
        
        # Start multiple threads making requests to different controllers
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=make_requests)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All should complete without server errors
        assert all(status < 500 for status in results)

    def test_memory_usage_large_responses(self, client, auth_headers, internal_headers):
        """Test memory usage with large responses across controllers"""
        with patch('src.application.use_cases.admin.get_security_stats_use_case.GetSecurityStatsUseCase.execute') as mock_stats:
            # Simulate large security stats response
            large_stats = {
                "security_statistics": {
                    "detailed_logs": [
                        {"event": f"event_{i}", "timestamp": f"2024-01-10T{i%24:02d}:00:00Z"}
                        for i in range(1000)
                    ]
                }
            }
            mock_stats.return_value = large_stats

            response = client.get('/api/admin/security-stats',
                headers=internal_headers)

            # Should handle large responses without memory issues
            assert response.status_code == 200
            data = response.get_json()
            assert len(data['security_statistics']['detailed_logs']) == 1000

    def test_error_handling_consistency(self, client, auth_headers):
        """Test consistent error handling across all controllers"""
        # Test various error scenarios
        error_endpoints = [
            ('/api/user/profile', 'user_error'),
            ('/api/generation/images/status/nonexistent', 'generation_error')
        ]

        for endpoint, error_type in error_endpoints:
            response = client.get(endpoint, headers=auth_headers)
            
            # All errors should return proper JSON format
            if response.status_code >= 400:
                data = response.get_json()
                assert isinstance(data, dict)
                # Should have consistent error structure
                assert 'error' in data or 'message' in data

    def test_data_validation_consistency(self, client, auth_headers):
        """Test consistent data validation across controllers"""
        # Test XSS protection across different endpoints
        xss_payload = "<script>alert('xss')</script>"
        
        test_data = [
            ('/api/user/profile', {'display_name': xss_payload}),
            ('/api/image_management/assign_image', {'ingredient_name': xss_payload})
        ]

        for endpoint, data in test_data:
            response = client.put(endpoint, json=data, headers=auth_headers)
            
            # Response should not contain unescaped script tags
            response_text = response.get_data(as_text=True)
            assert '<script>' not in response_text