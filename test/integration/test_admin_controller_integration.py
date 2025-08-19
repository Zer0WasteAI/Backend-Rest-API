"""
Integration tests for Admin Controller
Tests end-to-end administrative workflows and security features
"""
import pytest
import json
from datetime import datetime, date, timedelta
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token


class TestAdminControllerIntegration:
    """Integration test suite for Admin Controller"""
    
    @pytest.fixture
    def app(self):
        """Create Flask app for integration testing"""
        app = Flask(__name__)
        app.config['JWT_SECRET_KEY'] = 'test-secret'
        app.config['TESTING'] = True
        
        # Register admin blueprint
        from src.interface.controllers.admin_controller import admin_bp
        app.register_blueprint(admin_bp, url_prefix='/api/admin')
        
        # Initialize JWT
        jwt = JWTManager(app)
        
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    @pytest.fixture
    def admin_token(self, app):
        """Create admin authentication token"""
        with app.app_context():
            token = create_access_token(
                identity="admin-user-123",
                additional_claims={"role": "admin", "permissions": ["admin_access", "security_management"]}
            )
        return token
    
    @pytest.fixture
    def admin_headers(self, admin_token):
        """Create admin authentication headers"""
        return {"Authorization": f"Bearer {admin_token}"}
    
    @pytest.fixture
    def regular_user_token(self, app):
        """Create regular user token for authorization testing"""
        with app.app_context():
            token = create_access_token(identity="regular-user-123")
        return token
    
    @pytest.fixture
    def regular_user_headers(self, regular_user_token):
        """Create regular user headers"""
        return {"Authorization": f"Bearer {regular_user_token}"}

    # INTEGRATION TEST 1: Complete Token Cleanup Workflow
    @patch('src.interface.controllers.admin_controller.make_cleanup_expired_tokens_use_case')
    @patch('src.interface.controllers.admin_controller.make_get_security_stats_use_case')
    def test_complete_token_cleanup_workflow(
        self,
        mock_security_stats_use_case,
        mock_cleanup_use_case,
        client,
        admin_headers
    ):
        """Test complete token cleanup workflow: Get stats → Cleanup → Verify results"""
        
        # Step 1: Get initial security statistics
        initial_security_stats = {
            "token_statistics": {
                "total_active_tokens": 1250,
                "expired_tokens": 340,
                "tokens_expiring_soon": 89,  # Within 24 hours
                "invalid_tokens": 12,
                "blacklisted_tokens": 5
            },
            "user_statistics": {
                "total_active_users": 890,
                "users_with_expired_tokens": 156,
                "admin_users": 3,
                "suspended_users": 2
            },
            "security_metrics": {
                "failed_login_attempts_24h": 45,
                "successful_logins_24h": 2340,
                "suspicious_activities": 8,
                "security_alerts": ["Multiple failed logins from IP 192.168.1.100"]
            },
            "cleanup_recommendations": {
                "tokens_to_cleanup": 352,  # expired + invalid
                "estimated_storage_freed": "2.1 MB",
                "recommended_action": "immediate_cleanup"
            }
        }
        
        mock_security_stats_use_case.return_value.execute.return_value = initial_security_stats
        
        response = client.get("/api/admin/security-stats", headers=admin_headers)
        
        assert response.status_code == 200
        stats_data = response.get_json()
        assert stats_data["token_statistics"]["expired_tokens"] == 340
        assert stats_data["cleanup_recommendations"]["tokens_to_cleanup"] == 352
        
        # Step 2: Execute token cleanup
        cleanup_results = {
            "cleanup_id": "cleanup_2025_08_19_001",
            "executed_at": "2025-08-19T16:00:00Z",
            "cleanup_summary": {
                "expired_tokens_removed": 340,
                "invalid_tokens_removed": 12,
                "total_tokens_cleaned": 352,
                "storage_freed": "2.1 MB",
                "cleanup_duration_seconds": 15.7
            },
            "affected_users": {
                "users_notified": 156,
                "users_requiring_reauth": 156,
                "admin_users_affected": 0
            },
            "post_cleanup_stats": {
                "total_active_tokens": 898,  # Reduced from 1250
                "cleanup_efficiency": 99.7,
                "errors_encountered": 0
            },
            "next_cleanup_recommended": "2025-08-26T16:00:00Z"
        }
        
        mock_cleanup_use_case.return_value.execute.return_value = cleanup_results
        
        cleanup_request = {
            "cleanup_type": "expired_and_invalid",
            "force_cleanup": False,
            "notify_affected_users": True,
            "dry_run": False
        }
        
        response = client.post("/api/admin/cleanup-tokens",
                              json=cleanup_request,
                              headers=admin_headers)
        
        assert response.status_code == 200
        cleanup_data = response.get_json()
        assert cleanup_data["cleanup_summary"]["total_tokens_cleaned"] == 352
        assert cleanup_data["affected_users"]["users_notified"] == 156
        assert cleanup_data["post_cleanup_stats"]["cleanup_efficiency"] == 99.7
        
        # Step 3: Verify cleanup results with updated security stats
        updated_security_stats = initial_security_stats.copy()
        updated_security_stats["token_statistics"]["total_active_tokens"] = 898
        updated_security_stats["token_statistics"]["expired_tokens"] = 0
        updated_security_stats["token_statistics"]["invalid_tokens"] = 0
        updated_security_stats["cleanup_history"] = [
            {
                "cleanup_id": "cleanup_2025_08_19_001",
                "executed_at": "2025-08-19T16:00:00Z",
                "tokens_cleaned": 352
            }
        ]
        
        mock_security_stats_use_case.return_value.execute.return_value = updated_security_stats
        
        response = client.get("/api/admin/security-stats", headers=admin_headers)
        
        assert response.status_code == 200
        final_stats = response.get_json()
        assert final_stats["token_statistics"]["expired_tokens"] == 0
        assert final_stats["token_statistics"]["total_active_tokens"] == 898
        assert len(final_stats["cleanup_history"]) == 1

    # INTEGRATION TEST 2: Security Monitoring and Alerting
    @patch('src.interface.controllers.admin_controller.make_get_security_stats_use_case')
    def test_security_monitoring_integration(
        self,
        mock_security_stats_use_case,
        client,
        admin_headers
    ):
        """Test comprehensive security monitoring and alerting system"""
        
        # Mock comprehensive security statistics with alerts
        security_data = {
            "real_time_metrics": {
                "current_active_sessions": 456,
                "requests_per_minute": 890,
                "error_rate_percentage": 2.1,
                "average_response_time_ms": 145
            },
            "security_alerts": {
                "critical_alerts": [
                    {
                        "alert_id": "CRIT_001",
                        "type": "brute_force_attack",
                        "severity": "critical",
                        "description": "Multiple failed login attempts detected from IP 192.168.1.100",
                        "first_detected": "2025-08-19T15:30:00Z",
                        "attempts_count": 25,
                        "affected_endpoints": ["/api/auth/firebase-signin"],
                        "recommended_action": "Block IP address"
                    }
                ],
                "warning_alerts": [
                    {
                        "alert_id": "WARN_001",
                        "type": "unusual_traffic",
                        "severity": "warning",
                        "description": "Traffic spike detected from region: Eastern Europe",
                        "detected_at": "2025-08-19T15:45:00Z",
                        "traffic_increase_percentage": 340
                    }
                ],
                "info_alerts": [
                    {
                        "alert_id": "INFO_001",
                        "type": "system_maintenance",
                        "severity": "info",
                        "description": "Scheduled maintenance window approaching",
                        "scheduled_time": "2025-08-20T02:00:00Z"
                    }
                ]
            },
            "threat_detection": {
                "blocked_ips": ["192.168.1.100", "10.0.0.150"],
                "suspicious_user_agents": 3,
                "malformed_requests": 12,
                "sql_injection_attempts": 0,
                "xss_attempts": 2
            },
            "compliance_metrics": {
                "gdpr_compliance_score": 95,
                "data_retention_policy_violations": 0,
                "privacy_policy_adherence": 98,
                "audit_trail_completeness": 100
            },
            "performance_impact": {
                "security_overhead_ms": 8.5,
                "false_positive_rate": 0.02,
                "security_rules_active": 45
            }
        }
        
        mock_security_stats_use_case.return_value.execute.return_value = security_data
        
        response = client.get("/api/admin/security-stats", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["security_alerts"]["critical_alerts"]) == 1
        assert data["threat_detection"]["blocked_ips"][0] == "192.168.1.100"
        assert data["compliance_metrics"]["gdpr_compliance_score"] == 95
        assert data["performance_impact"]["security_overhead_ms"] == 8.5

    # INTEGRATION TEST 3: Admin Authorization and Access Control
    def test_admin_authorization_integration(
        self,
        client,
        admin_headers,
        regular_user_headers
    ):
        """Test admin endpoint authorization and access control"""
        
        # Test endpoints that require admin privileges
        admin_endpoints = [
            ("GET", "/api/admin/security-stats", None),
            ("POST", "/api/admin/cleanup-tokens", {"cleanup_type": "expired"})
        ]
        
        # Test with regular user (should be denied)
        for method, endpoint, data in admin_endpoints:
            if method == "GET":
                response = client.get(endpoint, headers=regular_user_headers)
            elif method == "POST":
                response = client.post(endpoint, json=data, headers=regular_user_headers)
                
            assert response.status_code in [401, 403], f"Regular user should be denied access to {endpoint}"
        
        # Test with admin user (should be allowed, though mocked responses may fail)
        for method, endpoint, data in admin_endpoints:
            if method == "GET":
                response = client.get(endpoint, headers=admin_headers)
            elif method == "POST":
                response = client.post(endpoint, json=data, headers=admin_headers)
                
            # Admin should at least not get 401/403 (may get 500 due to missing mocks)
            assert response.status_code not in [401, 403], f"Admin should have access to {endpoint}"

    # INTEGRATION TEST 4: Comprehensive Token Cleanup Scenarios
    @patch('src.interface.controllers.admin_controller.make_cleanup_expired_tokens_use_case')
    def test_comprehensive_token_cleanup_scenarios(
        self,
        mock_cleanup_use_case,
        client,
        admin_headers
    ):
        """Test various token cleanup scenarios and edge cases"""
        
        # Scenario 1: Dry run cleanup
        mock_cleanup_use_case.return_value.execute.return_value = {
            "dry_run": True,
            "cleanup_preview": {
                "expired_tokens": 150,
                "invalid_tokens": 8,
                "total_to_cleanup": 158,
                "estimated_storage_freed": "950 KB"
            },
            "affected_users_preview": {
                "users_affected": 89,
                "admin_users_affected": 0,
                "critical_services_affected": []
            },
            "recommendations": [
                "Proceed with cleanup - low risk",
                "Consider notifying users 1 hour before cleanup"
            ]
        }
        
        dry_run_request = {
            "cleanup_type": "expired_and_invalid",
            "dry_run": True
        }
        
        response = client.post("/api/admin/cleanup-tokens",
                              json=dry_run_request,
                              headers=admin_headers)
        
        assert response.status_code == 200
        dry_run_data = response.get_json()
        assert dry_run_data["dry_run"] is True
        assert dry_run_data["cleanup_preview"]["total_to_cleanup"] == 158
        
        # Scenario 2: Selective cleanup (only expired)
        mock_cleanup_use_case.return_value.execute.return_value = {
            "cleanup_type": "expired_only",
            "cleanup_summary": {
                "expired_tokens_removed": 150,
                "invalid_tokens_removed": 0,
                "total_tokens_cleaned": 150
            },
            "selective_cleanup": True
        }
        
        selective_request = {
            "cleanup_type": "expired_only",
            "force_cleanup": False
        }
        
        response = client.post("/api/admin/cleanup-tokens",
                              json=selective_request,
                              headers=admin_headers)
        
        assert response.status_code == 200
        selective_data = response.get_json()
        assert selective_data["selective_cleanup"] is True
        assert selective_data["cleanup_summary"]["expired_tokens_removed"] == 150
        
        # Scenario 3: Emergency cleanup with force option
        mock_cleanup_use_case.return_value.execute.return_value = {
            "cleanup_type": "emergency",
            "force_cleanup": True,
            "cleanup_summary": {
                "expired_tokens_removed": 340,
                "invalid_tokens_removed": 12,
                "suspicious_tokens_removed": 5,
                "total_tokens_cleaned": 357
            },
            "emergency_measures": {
                "immediate_execution": True,
                "user_notifications_skipped": True,
                "security_priority": True
            }
        }
        
        emergency_request = {
            "cleanup_type": "emergency",
            "force_cleanup": True,
            "notify_affected_users": False
        }
        
        response = client.post("/api/admin/cleanup-tokens",
                              json=emergency_request,
                              headers=admin_headers)
        
        assert response.status_code == 200
        emergency_data = response.get_json()
        assert emergency_data["force_cleanup"] is True
        assert emergency_data["emergency_measures"]["immediate_execution"] is True

    # INTEGRATION TEST 5: Security Stats Historical Data
    @patch('src.interface.controllers.admin_controller.make_get_security_stats_use_case')
    def test_security_stats_historical_integration(
        self,
        mock_security_stats_use_case,
        client,
        admin_headers
    ):
        """Test security statistics with historical data and trends"""
        
        mock_security_stats_use_case.return_value.execute.return_value = {
            "current_stats": {
                "total_active_tokens": 920,
                "failed_logins_24h": 23
            },
            "historical_data": {
                "daily_stats": [
                    {
                        "date": "2025-08-19",
                        "active_tokens": 920,
                        "failed_logins": 23,
                        "successful_logins": 1890,
                        "tokens_cleaned": 352
                    },
                    {
                        "date": "2025-08-18",
                        "active_tokens": 1272,
                        "failed_logins": 31,
                        "successful_logins": 1756,
                        "tokens_cleaned": 0
                    },
                    {
                        "date": "2025-08-17",
                        "active_tokens": 1198,
                        "failed_logins": 18,
                        "successful_logins": 1823,
                        "tokens_cleaned": 89
                    }
                ],
                "trends": {
                    "token_growth_rate": -2.1,  # Negative due to cleanup
                    "login_success_rate": 98.8,
                    "security_incidents_trend": "decreasing"
                }
            },
            "predictive_analytics": {
                "next_cleanup_recommended": "2025-08-26T16:00:00Z",
                "estimated_tokens_to_expire": 45,
                "projected_storage_usage": "15.2 MB"
            },
            "benchmark_comparisons": {
                "industry_average_success_rate": 97.2,
                "our_performance": "above_average",
                "security_score": 94
            }
        }
        
        response = client.get("/api/admin/security-stats?include_history=true",
                             headers=admin_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert "historical_data" in data
        assert len(data["historical_data"]["daily_stats"]) == 3
        assert data["historical_data"]["trends"]["login_success_rate"] == 98.8
        assert "predictive_analytics" in data

    # INTEGRATION TEST 6: Error Handling and Recovery
    @patch('src.interface.controllers.admin_controller.make_cleanup_expired_tokens_use_case')
    @patch('src.interface.controllers.admin_controller.make_get_security_stats_use_case')
    def test_admin_error_handling_integration(
        self,
        mock_security_stats_use_case,
        mock_cleanup_use_case,
        client,
        admin_headers
    ):
        """Test error handling and recovery scenarios in admin operations"""
        
        # Test cleanup failure with partial success
        mock_cleanup_use_case.return_value.execute.return_value = {
            "cleanup_status": "partial_failure",
            "cleanup_summary": {
                "expired_tokens_removed": 200,
                "invalid_tokens_removed": 0,  # Failed to process
                "total_tokens_cleaned": 200,
                "total_attempted": 340,
                "errors_encountered": 140
            },
            "error_details": [
                {
                    "error_type": "database_timeout",
                    "affected_tokens": 85,
                    "error_message": "Database query timeout while cleaning invalid tokens"
                },
                {
                    "error_type": "lock_contention",
                    "affected_tokens": 55,
                    "error_message": "Table lock contention during cleanup operation"
                }
            ],
            "recovery_actions": [
                "Retry cleanup for failed tokens in 30 minutes",
                "Consider scheduling cleanup during low-traffic hours"
            ]
        }
        
        response = client.post("/api/admin/cleanup-tokens",
                              json={"cleanup_type": "all"},
                              headers=admin_headers)
        
        assert response.status_code == 200  # Partial success still returns 200
        data = response.get_json()
        assert data["cleanup_status"] == "partial_failure"
        assert len(data["error_details"]) == 2
        assert len(data["recovery_actions"]) == 2
        
        # Test service degradation scenario
        mock_security_stats_use_case.return_value.execute.return_value = {
            "service_status": "degraded",
            "available_metrics": {
                "basic_token_stats": {"total_active_tokens": 950},
                "limited_security_data": True
            },
            "unavailable_metrics": [
                "real_time_monitoring",
                "detailed_threat_analysis"
            ],
            "degradation_reason": "High database load affecting complex queries",
            "estimated_recovery_time": "15 minutes"
        }
        
        response = client.get("/api/admin/security-stats", headers=admin_headers)
        
        assert response.status_code == 200  # Still provides basic service
        stats_data = response.get_json()
        assert stats_data["service_status"] == "degraded"
        assert "estimated_recovery_time" in stats_data

    # INTEGRATION TEST 7: Authentication Requirements
    def test_admin_authentication_requirements(self, client):
        """Test that admin endpoints require proper authentication"""
        
        admin_endpoints = [
            ("GET", "/api/admin/security-stats"),
            ("POST", "/api/admin/cleanup-tokens")
        ]
        
        for method, endpoint in admin_endpoints:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint, json={})
                
            assert response.status_code == 401, f"Endpoint {method} {endpoint} should require authentication"
