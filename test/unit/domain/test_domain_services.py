"""
Unit tests for Domain Services
Tests business logic services in the domain layer
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, date


class TestDomainServices:
    """Test suite for Domain Services"""

    # Auth Service Tests
    def test_auth_service_user_validation(self):
        """Test auth service user validation"""
        # Arrange
        from src.domain.services.auth_service import AuthService
        
        service = AuthService()
        user_data = {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "display_name": "Test User"
        }
        
        # Act
        validation_result = service.validate_user_credentials(user_data)
        
        # Assert
        assert "is_valid" in validation_result
        assert isinstance(validation_result["is_valid"], bool)

    def test_auth_service_password_strength(self):
        """Test auth service password strength validation"""
        # Arrange
        from src.domain.services.auth_service import AuthService
        
        service = AuthService()
        
        # Act
        weak_result = service.check_password_strength("123456")
        strong_result = service.check_password_strength("SecurePass123!")
        
        # Assert
        assert weak_result["strength"] in ["weak", "medium", "strong"]
        assert strong_result["strength"] in ["medium", "strong"]

    # Email Service Tests
    @patch('src.domain.services.email_service.smtp_client')
    def test_email_service_send_notification(self, mock_smtp):
        """Test email service notification sending"""
        # Arrange
        from src.domain.services.email_service import EmailService
        
        mock_smtp.send_message.return_value = True
        service = EmailService()
        
        # Act
        result = service.send_notification_email(
            to_email="test@example.com",
            subject="Test Notification",
            message="This is a test message"
        )
        
        # Assert
        assert result is True
        mock_smtp.send_message.assert_called()

    @patch('src.domain.services.email_service.smtp_client')
    def test_email_service_recipe_sharing(self, mock_smtp):
        """Test email service recipe sharing functionality"""
        # Arrange
        from src.domain.services.email_service import EmailService
        
        mock_smtp.send_message.return_value = True
        service = EmailService()
        
        recipe_data = {
            "title": "Tomato Soup",
            "ingredients": ["Tomato", "Onion", "Garlic"],
            "instructions": ["Sauté onions", "Add tomatoes", "Simmer"]
        }
        
        # Act
        result = service.send_recipe_email("friend@example.com", recipe_data)
        
        # Assert
        assert result is True
        mock_smtp.send_message.assert_called()

    # SMS Service Tests
    @patch('src.domain.services.sms_service.twilio_client')
    def test_sms_service_expiry_reminder(self, mock_twilio):
        """Test SMS service expiry reminder functionality"""
        # Arrange
        from src.domain.services.sms_service import SMSService
        
        mock_twilio.messages.create.return_value = Mock(sid="test_sid")
        service = SMSService()
        
        # Act
        result = service.send_expiry_reminder(
            phone_number="+1234567890",
            items=["Milk", "Bread"]
        )
        
        # Assert
        assert "message_id" in result
        mock_twilio.messages.create.assert_called()

    @patch('src.domain.services.sms_service.twilio_client')
    def test_sms_service_cooking_timer(self, mock_twilio):
        """Test SMS service cooking timer notifications"""
        # Arrange
        from src.domain.services.sms_service import SMSService
        
        mock_twilio.messages.create.return_value = Mock(sid="test_sid")
        service = SMSService()
        
        # Act
        result = service.send_cooking_timer_alert(
            phone_number="+1234567890",
            recipe_name="Tomato Soup",
            step="Remove from heat"
        )
        
        # Assert
        assert "message_id" in result
        mock_twilio.messages.create.assert_called()

    # OAuth Service Tests
    def test_oauth_service_google_auth_url(self):
        """Test OAuth service Google authentication URL generation"""
        # Arrange
        from src.domain.services.oauth_service import OAuthService
        
        service = OAuthService()
        
        # Act
        auth_url = service.get_google_auth_url(redirect_uri="http://localhost:5000/callback")
        
        # Assert
        assert "https://accounts.google.com/oauth2" in auth_url
        assert "redirect_uri" in auth_url
        assert "scope" in auth_url

    @patch('src.domain.services.oauth_service.google_oauth')
    def test_oauth_service_token_exchange(self, mock_oauth):
        """Test OAuth service authorization code to token exchange"""
        # Arrange
        from src.domain.services.oauth_service import OAuthService
        
        mock_oauth.fetch_token.return_value = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token"
        }
        service = OAuthService()
        
        # Act
        tokens = service.exchange_code_for_tokens("test_auth_code")
        
        # Assert
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        mock_oauth.fetch_token.assert_called()

    # AI Food Analyzer Service Tests
    @patch('src.domain.services.ia_food_analyzer_service.ai_client')
    def test_ia_food_analyzer_nutritional_analysis(self, mock_ai):
        """Test AI food analyzer nutritional analysis"""
        # Arrange
        from src.domain.services.ia_food_analyzer_service import IAFoodAnalyzerService
        
        mock_ai.analyze.return_value = {
            "calories": 150,
            "protein": 8.0,
            "carbs": 20.0,
            "fat": 5.0
        }
        service = IAFoodAnalyzerService()
        
        # Act
        analysis = service.analyze_food_nutrition("Apple", quantity=100, unit="g")
        
        # Assert
        assert "calories" in analysis
        assert analysis["calories"] == 150
        mock_ai.analyze.assert_called()

    @patch('src.domain.services.ia_food_analyzer_service.ai_client')
    def test_ia_food_analyzer_freshness_assessment(self, mock_ai):
        """Test AI food analyzer freshness assessment"""
        # Arrange
        from src.domain.services.ia_food_analyzer_service import IAFoodAnalyzerService
        
        mock_ai.assess_freshness.return_value = {
            "freshness_score": 85,
            "estimated_shelf_life": 5,
            "quality_indicators": ["good_color", "firm_texture"]
        }
        service = IAFoodAnalyzerService()
        
        # Act
        freshness = service.assess_food_freshness("image_data", food_type="Tomato")
        
        # Assert
        assert "freshness_score" in freshness
        assert freshness["freshness_score"] == 85
        mock_ai.assess_freshness.assert_called()

    # AI Recipe Generator Service Tests
    @patch('src.domain.services.ia_recipe_generator_service.ai_client')
    def test_ia_recipe_generator_create_recipe(self, mock_ai):
        """Test AI recipe generator recipe creation"""
        # Arrange
        from src.domain.services.ia_recipe_generator_service import IARecipeGeneratorService
        
        mock_ai.generate_recipe.return_value = {
            "title": "Vegetable Stir Fry",
            "ingredients": [
                {"name": "Broccoli", "amount": 200, "unit": "g"},
                {"name": "Carrot", "amount": 100, "unit": "g"}
            ],
            "instructions": ["Heat oil", "Add vegetables", "Stir fry for 5 minutes"]
        }
        service = IARecipeGeneratorService()
        
        # Act
        recipe = service.generate_recipe_from_ingredients(["Broccoli", "Carrot", "Soy Sauce"])
        
        # Assert
        assert "title" in recipe
        assert "ingredients" in recipe
        assert "instructions" in recipe
        mock_ai.generate_recipe.assert_called()

    @patch('src.domain.services.ia_recipe_generator_service.ai_client')
    def test_ia_recipe_generator_dietary_customization(self, mock_ai):
        """Test AI recipe generator dietary customization"""
        # Arrange
        from src.domain.services.ia_recipe_generator_service import IARecipeGeneratorService
        
        mock_ai.customize_recipe.return_value = {
            "title": "Vegan Pasta Primavera",
            "dietary_compliance": ["vegan", "dairy_free"],
            "substitutions_made": [
                {"original": "Parmesan cheese", "substitute": "Nutritional yeast"}
            ]
        }
        service = IARecipeGeneratorService()
        
        # Act
        customized = service.customize_recipe_for_diet(
            recipe_id=1,
            dietary_restrictions=["vegan"],
            preferences={"cuisine": "italian"}
        )
        
        # Assert
        assert "dietary_compliance" in customized
        assert "vegan" in customized["dietary_compliance"]
        mock_ai.customize_recipe.assert_called()

    # Inventory Calculator Service Tests
    def test_inventory_calculator_expiry_prediction(self):
        """Test inventory calculator expiry date prediction"""
        # Arrange
        from src.domain.services.inventory_calculator import InventoryCalculator
        
        calculator = InventoryCalculator()
        item_data = {
            "name": "Banana",
            "purchase_date": "2024-01-01",
            "category": "fruits",
            "storage_condition": "room_temperature"
        }
        
        # Act
        expiry_prediction = calculator.predict_expiry_date(item_data)
        
        # Assert
        assert "predicted_expiry" in expiry_prediction
        assert "confidence" in expiry_prediction
        assert isinstance(expiry_prediction["confidence"], (int, float))

    def test_inventory_calculator_waste_risk_assessment(self):
        """Test inventory calculator waste risk assessment"""
        # Arrange
        from src.domain.services.inventory_calculator import InventoryCalculator
        
        calculator = InventoryCalculator()
        inventory_items = [
            {"name": "Milk", "expiry_date": "2024-01-15", "quantity": 1},
            {"name": "Bread", "expiry_date": "2024-01-20", "quantity": 1},
            {"name": "Apples", "expiry_date": "2024-02-01", "quantity": 6}
        ]
        
        # Act
        risk_assessment = calculator.assess_waste_risk(inventory_items)
        
        # Assert
        assert "high_risk_items" in risk_assessment
        assert "total_risk_score" in risk_assessment
        assert isinstance(risk_assessment["total_risk_score"], (int, float))

    def test_inventory_calculator_optimal_usage_order(self):
        """Test inventory calculator optimal usage order recommendation"""
        # Arrange
        from src.domain.services.inventory_calculator import InventoryCalculator
        
        calculator = InventoryCalculator()
        items = [
            {"name": "Yogurt", "expiry_date": "2024-01-18", "category": "dairy"},
            {"name": "Lettuce", "expiry_date": "2024-01-16", "category": "vegetables"},
            {"name": "Pasta", "expiry_date": "2024-12-01", "category": "grains"}
        ]
        
        # Act
        usage_order = calculator.recommend_usage_order(items)
        
        # Assert
        assert isinstance(usage_order, list)
        assert len(usage_order) == 3
        # First item should be the one expiring soonest
        assert usage_order[0]["name"] == "Lettuce"
