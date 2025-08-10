"""
Unit tests for SMSService abstract interface
Tests the contract and behavior expectations for SMS service implementations
"""
import pytest
from abc import ABCMeta
from unittest.mock import Mock

from src.domain.services.sms_service import SMSService


class TestSMSService:
    """Test suite for SMSService abstract interface"""
    
    def test_sms_service_is_abstract(self):
        """Test that SMSService is an abstract base class"""
        # Act & Assert
        assert SMSService.__bases__ == (ABCMeta,)
        
        # Should not be able to instantiate directly
        with pytest.raises(TypeError):
            SMSService()
    
    def test_send_otp_is_abstract_method(self):
        """Test that send_otp is defined as abstract method"""
        # Arrange
        abstract_methods = SMSService.__abstractmethods__
        
        # Assert
        assert 'send_otp' in abstract_methods
    
    def test_send_otp_signature_and_documentation(self):
        """Test send_otp method signature and documentation"""
        # Arrange
        method = SMSService.send_otp
        
        # Assert
        assert hasattr(SMSService, 'send_otp')
        assert method.__doc__ is not None
        assert 'Envia un código OTP al número de teléfono' in method.__doc__
        assert ':param phone: Número de teléfono' in method.__doc__
        assert ':param code: Codigo OTP a enviar' in method.__doc__
        assert ':raises SMSDeliveryException' in method.__doc__


class ConcreteSMSService(SMSService):
    """Concrete implementation for testing purposes"""
    
    def __init__(self):
        self.sent_messages = []
        self.delivery_failures = []
        self.blocked_numbers = ["+1234567890"]  # Simulate blocked numbers
    
    def send_otp(self, phone: str, code: str):
        """Mock implementation for SMS OTP sending"""
        # Validate inputs
        if not phone:
            raise ValueError("Phone number cannot be empty")
        
        if not code:
            raise ValueError("OTP code cannot be empty")
        
        # Check for blocked numbers
        if phone in self.blocked_numbers:
            self.delivery_failures.append({
                "phone": phone,
                "code": code,
                "error": "blocked_number",
                "message": "Phone number is blocked"
            })
            raise Exception(f"SMS delivery failed: Phone number {phone} is blocked")
        
        # Simulate different phone number scenarios
        if phone.startswith("+999"):
            # Simulate network error
            self.delivery_failures.append({
                "phone": phone,
                "code": code,
                "error": "network_error",
                "message": "Network timeout"
            })
            raise Exception("SMS delivery failed: Network timeout")
        
        elif phone.startswith("+888"):
            # Simulate invalid phone number
            self.delivery_failures.append({
                "phone": phone,
                "code": code,
                "error": "invalid_number",
                "message": "Invalid phone number format"
            })
            raise Exception(f"SMS delivery failed: Invalid phone number {phone}")
        
        elif len(phone) < 10:
            # Simulate too short number
            self.delivery_failures.append({
                "phone": phone,
                "code": code,
                "error": "invalid_format",
                "message": "Phone number too short"
            })
            raise Exception("SMS delivery failed: Phone number too short")
        
        # Successful delivery
        message_record = {
            "phone": phone,
            "code": code,
            "timestamp": "2024-01-01T12:00:00Z",
            "status": "delivered",
            "message_id": f"msg_{len(self.sent_messages) + 1}"
        }
        
        self.sent_messages.append(message_record)
        return f"OTP {code} sent successfully to {phone}"


class TestConcreteSMSService:
    """Test suite for concrete SMSService implementation"""
    
    @pytest.fixture
    def sms_service(self):
        """Concrete SMS service for testing"""
        return ConcreteSMSService()
    
    def test_concrete_implementation_can_be_instantiated(self, sms_service):
        """Test that concrete implementation can be created"""
        # Assert
        assert isinstance(sms_service, SMSService)
        assert isinstance(sms_service, ConcreteSMSService)
        assert len(sms_service.sent_messages) == 0
        assert len(sms_service.delivery_failures) == 0
    
    def test_send_otp_successful_delivery(self, sms_service):
        """Test successful OTP SMS delivery"""
        # Arrange
        phone = "+1234567891"  # Not in blocked list
        code = "123456"
        
        # Act
        result = sms_service.send_otp(phone, code)
        
        # Assert
        assert "sent successfully" in result
        assert phone in result
        assert code in result
        
        # Verify message was recorded
        assert len(sms_service.sent_messages) == 1
        sent_message = sms_service.sent_messages[0]
        assert sent_message["phone"] == phone
        assert sent_message["code"] == code
        assert sent_message["status"] == "delivered"
        assert "message_id" in sent_message
    
    @pytest.mark.parametrize("phone,code", [
        ("+5551234567", "111111"),
        ("+44987654321", "999999"), 
        ("+81901234567", "456789"),
        ("+33123456789", "000000"),
    ])
    def test_send_otp_multiple_successful_scenarios(self, sms_service, phone, code):
        """Parametrized test for successful OTP sending to different numbers"""
        # Act
        result = sms_service.send_otp(phone, code)
        
        # Assert
        assert "sent successfully" in result
        assert phone in result
        assert code in result
        
        # Verify in sent messages
        assert any(msg["phone"] == phone and msg["code"] == code 
                  for msg in sms_service.sent_messages)
    
    def test_send_otp_with_empty_phone(self, sms_service):
        """Test OTP sending with empty phone number"""
        # Arrange
        phone = ""
        code = "123456"
        
        # Act & Assert
        with pytest.raises(ValueError, match="Phone number cannot be empty"):
            sms_service.send_otp(phone, code)
        
        # Verify no messages were sent
        assert len(sms_service.sent_messages) == 0
    
    def test_send_otp_with_empty_code(self, sms_service):
        """Test OTP sending with empty code"""
        # Arrange
        phone = "+1234567891"
        code = ""
        
        # Act & Assert
        with pytest.raises(ValueError, match="OTP code cannot be empty"):
            sms_service.send_otp(phone, code)
        
        # Verify no messages were sent
        assert len(sms_service.sent_messages) == 0
    
    def test_send_otp_to_blocked_number(self, sms_service):
        """Test OTP sending to blocked phone number"""
        # Arrange
        phone = "+1234567890"  # This is in blocked_numbers list
        code = "123456"
        
        # Act & Assert
        with pytest.raises(Exception, match="Phone number .* is blocked"):
            sms_service.send_otp(phone, code)
        
        # Verify failure was recorded
        assert len(sms_service.delivery_failures) == 1
        failure = sms_service.delivery_failures[0]
        assert failure["phone"] == phone
        assert failure["code"] == code
        assert failure["error"] == "blocked_number"
        
        # Verify no successful messages
        assert len(sms_service.sent_messages) == 0
    
    def test_send_otp_network_error_simulation(self, sms_service):
        """Test OTP sending with network error"""
        # Arrange
        phone = "+9991234567"  # Numbers starting with +999 simulate network error
        code = "123456"
        
        # Act & Assert
        with pytest.raises(Exception, match="Network timeout"):
            sms_service.send_otp(phone, code)
        
        # Verify failure was recorded
        assert len(sms_service.delivery_failures) == 1
        failure = sms_service.delivery_failures[0]
        assert failure["error"] == "network_error"
        assert failure["message"] == "Network timeout"
    
    def test_send_otp_invalid_number_format(self, sms_service):
        """Test OTP sending with invalid phone number format"""
        # Arrange
        phone = "+8881234567"  # Numbers starting with +888 simulate invalid format
        code = "123456"
        
        # Act & Assert
        with pytest.raises(Exception, match="Invalid phone number"):
            sms_service.send_otp(phone, code)
        
        # Verify failure was recorded
        assert len(sms_service.delivery_failures) == 1
        failure = sms_service.delivery_failures[0]
        assert failure["error"] == "invalid_number"
    
    def test_send_otp_phone_number_too_short(self, sms_service):
        """Test OTP sending with phone number that's too short"""
        # Arrange
        phone = "+123"  # Too short
        code = "123456"
        
        # Act & Assert
        with pytest.raises(Exception, match="Phone number too short"):
            sms_service.send_otp(phone, code)
        
        # Verify failure was recorded
        assert len(sms_service.delivery_failures) == 1
        failure = sms_service.delivery_failures[0]
        assert failure["error"] == "invalid_format"
    
    def test_multiple_otp_sends_tracking(self, sms_service):
        """Test that multiple OTP sends are properly tracked"""
        # Arrange
        sends = [
            ("+5551111111", "111111"),
            ("+5552222222", "222222"),
            ("+5553333333", "333333"),
        ]
        
        # Act
        for phone, code in sends:
            sms_service.send_otp(phone, code)
        
        # Assert
        assert len(sms_service.sent_messages) == 3
        
        for i, (phone, code) in enumerate(sends):
            message = sms_service.sent_messages[i]
            assert message["phone"] == phone
            assert message["code"] == code
            assert message["status"] == "delivered"
            assert message["message_id"] == f"msg_{i + 1}"
    
    def test_mixed_successful_and_failed_sends(self, sms_service):
        """Test mixture of successful and failed SMS sends"""
        # Arrange
        attempts = [
            ("+5551111111", "111111"),  # Should succeed
            ("+1234567890", "222222"),  # Should fail (blocked)
            ("+5553333333", "333333"),  # Should succeed
            ("+9991111111", "444444"),  # Should fail (network error)
        ]
        
        # Act & Assert
        successful_count = 0
        failed_count = 0
        
        for phone, code in attempts:
            try:
                sms_service.send_otp(phone, code)
                successful_count += 1
            except Exception:
                failed_count += 1
        
        # Assert final state
        assert successful_count == 2
        assert failed_count == 2
        assert len(sms_service.sent_messages) == 2
        assert len(sms_service.delivery_failures) == 2
    
    def test_otp_code_formats(self, sms_service):
        """Test OTP sending with different code formats"""
        # Arrange
        phone = "+5551234567"
        test_codes = [
            "123456",      # Standard 6-digit
            "1234",        # 4-digit
            "12345678",    # 8-digit  
            "ABC123",      # Alphanumeric
            "000000",      # All zeros
        ]
        
        # Act & Assert
        for code in test_codes:
            result = sms_service.send_otp(phone, code)
            assert code in result
            
        # Verify all were sent
        assert len(sms_service.sent_messages) == len(test_codes)
        sent_codes = [msg["code"] for msg in sms_service.sent_messages]
        assert sent_codes == test_codes
    
    def test_phone_number_formats(self, sms_service):
        """Test OTP sending with different phone number formats"""
        # Arrange
        code = "123456"
        test_phones = [
            "+15551234567",    # US format
            "+442012345678",   # UK format
            "+81901234567",    # Japan format
            "+33123456789",    # France format
            "+551234567890",   # Brazil format
        ]
        
        # Act & Assert
        for phone in test_phones:
            result = sms_service.send_otp(phone, code)
            assert phone in result
        
        # Verify all were sent
        assert len(sms_service.sent_messages) == len(test_phones)
        sent_phones = [msg["phone"] for msg in sms_service.sent_messages]
        assert sent_phones == test_phones
    
    def test_message_id_uniqueness(self, sms_service):
        """Test that each SMS gets a unique message ID"""
        # Arrange
        phone = "+5551234567"
        codes = ["111111", "222222", "333333"]
        
        # Act
        for code in codes:
            sms_service.send_otp(phone, code)
        
        # Assert
        message_ids = [msg["message_id"] for msg in sms_service.sent_messages]
        assert len(set(message_ids)) == len(message_ids)  # All IDs should be unique
        
        # Verify sequential numbering
        expected_ids = [f"msg_{i+1}" for i in range(len(codes))]
        assert message_ids == expected_ids


class FailingSMSService(SMSService):
    """SMS service that always fails for testing"""
    
    def send_otp(self, phone: str, code: str):
        """Implementation that always fails"""
        raise Exception("SMS service unavailable")


class TestSMSServiceErrorHandling:
    """Test suite for SMS service error scenarios"""
    
    @pytest.fixture
    def failing_sms_service(self):
        """SMS service that always fails"""
        return FailingSMSService()
    
    def test_sms_service_exception_handling(self, failing_sms_service):
        """Test that SMS service exceptions are properly raised"""
        # Act & Assert
        with pytest.raises(Exception, match="SMS service unavailable"):
            failing_sms_service.send_otp("+1234567890", "123456")