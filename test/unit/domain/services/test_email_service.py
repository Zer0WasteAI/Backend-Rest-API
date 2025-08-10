"""
Unit tests for EmailService abstract interface
Tests the contract and behavior expectations for email service implementations
"""
import pytest
from abc import ABCMeta
from src.domain.services.email_service import EmailService


class TestEmailService:
    """Test suite for EmailService abstract interface"""
    
    def test_email_service_is_abstract(self):
        """Test that EmailService is an abstract base class"""
        # Act & Assert
        assert EmailService.__bases__ == (ABCMeta,)
        
        # Should not be able to instantiate directly
        with pytest.raises(TypeError):
            EmailService()
    
    def test_send_otp_is_abstract_method(self):
        """Test that send_otp is defined as abstract method"""
        # Arrange
        abstract_methods = EmailService.__abstractmethods__
        
        # Assert
        assert 'send_otp' in abstract_methods
    
    def test_send_otp_signature(self):
        """Test send_otp method signature and documentation"""
        # Arrange
        send_otp_method = EmailService.send_otp
        
        # Assert method exists and has proper signature
        assert hasattr(EmailService, 'send_otp')
        assert send_otp_method.__doc__ is not None
        assert 'Send an OTP code' in send_otp_method.__doc__
        assert ':param to: The recipient\'s email address.' in send_otp_method.__doc__
        assert ':param code: The OTP code to send.' in send_otp_method.__doc__


class ConcreteEmailService(EmailService):
    """Concrete implementation for testing purposes"""
    
    def __init__(self):
        self.sent_emails = []
    
    def send_otp(self, to: str, code: str):
        """Test implementation that records sent emails"""
        self.sent_emails.append({"to": to, "code": code})
        return f"OTP {code} sent to {to}"


class TestConcreteEmailServiceImplementation:
    """Test suite for concrete EmailService implementation"""
    
    @pytest.fixture
    def email_service(self):
        """Concrete email service for testing"""
        return ConcreteEmailService()
    
    def test_concrete_implementation_can_be_instantiated(self, email_service):
        """Test that concrete implementation can be created"""
        # Assert
        assert isinstance(email_service, EmailService)
        assert isinstance(email_service, ConcreteEmailService)
    
    def test_send_otp_implementation(self, email_service):
        """Test concrete send_otp implementation"""
        # Arrange
        to_email = "test@example.com"
        otp_code = "123456"
        
        # Act
        result = email_service.send_otp(to_email, otp_code)
        
        # Assert
        assert result == f"OTP {otp_code} sent to {to_email}"
        assert len(email_service.sent_emails) == 1
        assert email_service.sent_emails[0]["to"] == to_email
        assert email_service.sent_emails[0]["code"] == otp_code
    
    @pytest.mark.parametrize("email,code", [
        ("user@example.com", "111111"),
        ("test@domain.org", "999999"),
        ("admin@company.co.uk", "456789"),
    ])
    def test_send_otp_multiple_scenarios(self, email_service, email, code):
        """Parametrized test for different email and code combinations"""
        # Act
        result = email_service.send_otp(email, code)
        
        # Assert
        assert code in result
        assert email in result
        assert any(sent["to"] == email and sent["code"] == code 
                  for sent in email_service.sent_emails)
    
    def test_send_otp_multiple_calls(self, email_service):
        """Test multiple OTP sends are recorded"""
        # Arrange
        emails_and_codes = [
            ("user1@test.com", "111111"),
            ("user2@test.com", "222222"),
            ("user3@test.com", "333333"),
        ]
        
        # Act
        for email, code in emails_and_codes:
            email_service.send_otp(email, code)
        
        # Assert
        assert len(email_service.sent_emails) == 3
        for i, (email, code) in enumerate(emails_and_codes):
            assert email_service.sent_emails[i]["to"] == email
            assert email_service.sent_emails[i]["code"] == code
    
    def test_send_otp_with_empty_values(self, email_service):
        """Test send_otp behavior with empty values"""
        # Act
        result1 = email_service.send_otp("", "123456")
        result2 = email_service.send_otp("test@example.com", "")
        
        # Assert
        assert len(email_service.sent_emails) == 2
        assert email_service.sent_emails[0]["to"] == ""
        assert email_service.sent_emails[0]["code"] == "123456"
        assert email_service.sent_emails[1]["to"] == "test@example.com"
        assert email_service.sent_emails[1]["code"] == ""


class FailingEmailService(EmailService):
    """Email service that fails for testing error scenarios"""
    
    def send_otp(self, to: str, code: str):
        raise Exception("Email service unavailable")


class TestEmailServiceErrorHandling:
    """Test suite for email service error scenarios"""
    
    @pytest.fixture
    def failing_service(self):
        """Email service that always fails"""
        return FailingEmailService()
    
    def test_email_service_exception_handling(self, failing_service):
        """Test that email service exceptions are properly raised"""
        # Act & Assert
        with pytest.raises(Exception, match="Email service unavailable"):
            failing_service.send_otp("test@example.com", "123456")