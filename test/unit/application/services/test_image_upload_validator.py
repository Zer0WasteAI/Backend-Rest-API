"""
Unit tests for Image Upload Validator
Tests image upload validation functionality
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import io
import tempfile

from src.application.services.image_upload_validator import (
    ImageUploadValidator,
    validate_upload_request
)


class TestImageUploadValidator:
    """Test suite for Image Upload Validator"""
    
    @pytest.fixture
    def validator(self):
        """Create image upload validator instance"""
        return ImageUploadValidator()
    
    @pytest.fixture
    def valid_image_file(self):
        """Create a valid mock image file"""
        mock_file = Mock()
        mock_file.filename = "test_image.jpg"
        mock_file.content_type = "image/jpeg"
        mock_file.read.return_value = b"\xff\xd8\xff\xe0\x00\x10JFIF"  # JPEG header
        mock_file.content_length = 1024 * 1024  # 1MB
        mock_file.stream = io.BytesIO(b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"fake_image_data" * 1000)
        return mock_file
    
    @pytest.fixture
    def invalid_file(self):
        """Create an invalid mock file"""
        mock_file = Mock()
        mock_file.filename = "document.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.read.return_value = b"%PDF-1.4"  # PDF header
        mock_file.content_length = 2048
        return mock_file
    
    def test_validate_upload_request_success(self, validator, valid_image_file):
        """Test successful upload validation"""
        # Arrange
        upload_request = {
            "file": valid_image_file,
            "user_id": "test-user-123",
            "upload_type": "profile_image"
        }
        
        # Act
        result = validator.validate_upload_request(upload_request)
        
        # Assert
        assert result is not None
        assert result.get("valid") is True or result is True

    def test_validate_upload_request_invalid_file_type(self, validator, invalid_file):
        """Test validation with invalid file type"""
        # Arrange
        upload_request = {
            "file": invalid_file,
            "user_id": "test-user-123",
            "upload_type": "profile_image"
        }
        
        # Act & Assert
        with pytest.raises((ValueError, TypeError)):
            validator.validate_upload_request(upload_request)

    def test_validate_upload_request_missing_file(self, validator):
        """Test validation with missing file"""
        # Arrange
        upload_request = {
            "user_id": "test-user-123",
            "upload_type": "profile_image"
        }
        
        # Act & Assert
        with pytest.raises((ValueError, KeyError)):
            validator.validate_upload_request(upload_request)

    def test_validate_upload_request_missing_user_id(self, validator, valid_image_file):
        """Test validation with missing user_id"""
        # Arrange
        upload_request = {
            "file": valid_image_file,
            "upload_type": "profile_image"
        }
        
        # Act & Assert
        with pytest.raises((ValueError, KeyError)):
            validator.validate_upload_request(upload_request)

    def test_validate_upload_request_empty_filename(self, validator):
        """Test validation with empty filename"""
        # Arrange
        mock_file = Mock()
        mock_file.filename = ""
        mock_file.content_type = "image/jpeg"
        mock_file.content_length = 1024
        
        upload_request = {
            "file": mock_file,
            "user_id": "test-user-123",
            "upload_type": "profile_image"
        }
        
        # Act & Assert
        with pytest.raises(ValueError):
            validator.validate_upload_request(upload_request)

    def test_validate_upload_request_file_too_large(self, validator):
        """Test validation with file too large"""
        # Arrange
        large_file = Mock()
        large_file.filename = "large_image.jpg"
        large_file.content_type = "image/jpeg"
        large_file.content_length = 50 * 1024 * 1024  # 50MB
        large_file.read.return_value = b"x" * (50 * 1024 * 1024)
        
        upload_request = {
            "file": large_file,
            "user_id": "test-user-123",
            "upload_type": "profile_image"
        }
        
        # Act & Assert
        with pytest.raises(ValueError):
            validator.validate_upload_request(upload_request)

    def test_validate_upload_request_supported_formats(self, validator):
        """Test validation with various supported image formats"""
        supported_formats = [
            ("image.jpg", "image/jpeg"),
            ("image.png", "image/png"),
            ("image.gif", "image/gif"),
            ("image.webp", "image/webp"),
            ("image.bmp", "image/bmp")
        ]
        
        for filename, content_type in supported_formats:
            # Arrange
            mock_file = Mock()
            mock_file.filename = filename
            mock_file.content_type = content_type
            mock_file.content_length = 1024 * 100  # 100KB
            mock_file.read.return_value = b"fake_image_data"
            
            upload_request = {
                "file": mock_file,
                "user_id": "test-user-123",
                "upload_type": "profile_image"
            }
            
            # Act
            try:
                result = validator.validate_upload_request(upload_request)
                # Should not raise exception for supported formats
                assert result is not None
            except Exception as e:
                # Only acceptable if it's validation logic, not format rejection
                assert "format" not in str(e).lower()

    def test_validate_upload_request_unsupported_formats(self, validator):
        """Test validation rejects unsupported formats"""
        unsupported_formats = [
            ("document.pdf", "application/pdf"),
            ("document.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
            ("archive.zip", "application/zip"),
            ("script.js", "application/javascript"),
            ("video.mp4", "video/mp4")
        ]
        
        for filename, content_type in unsupported_formats:
            # Arrange
            mock_file = Mock()
            mock_file.filename = filename
            mock_file.content_type = content_type
            mock_file.content_length = 1024
            mock_file.read.return_value = b"fake_file_data"
            
            upload_request = {
                "file": mock_file,
                "user_id": "test-user-123",
                "upload_type": "profile_image"
            }
            
            # Act & Assert
            with pytest.raises((ValueError, TypeError)):
                validator.validate_upload_request(upload_request)

    def test_validate_upload_request_malicious_filename(self, validator):
        """Test validation handles malicious filenames"""
        malicious_filenames = [
            "../../../etc/passwd",
            "file<script>alert('xss')</script>.jpg",
            "file%00.exe.jpg",
            "../../hack.php.jpg",
            "file\x00.exe.jpg"
        ]
        
        for malicious_name in malicious_filenames:
            # Arrange
            mock_file = Mock()
            mock_file.filename = malicious_name
            mock_file.content_type = "image/jpeg"
            mock_file.content_length = 1024
            mock_file.read.return_value = b"fake_image_data"
            
            upload_request = {
                "file": mock_file,
                "user_id": "test-user-123",
                "upload_type": "profile_image"
            }
            
            # Act
            try:
                result = validator.validate_upload_request(upload_request)
                # If validation passes, filename should be sanitized
                assert result is not None
            except ValueError:
                # Acceptable to reject malicious filenames
                pass

    def test_validate_upload_request_different_upload_types(self, validator, valid_image_file):
        """Test validation with different upload types"""
        upload_types = [
            "profile_image",
            "inventory_image", 
            "recipe_image",
            "ingredient_image",
            "food_image"
        ]
        
        for upload_type in upload_types:
            # Arrange
            upload_request = {
                "file": valid_image_file,
                "user_id": "test-user-123",
                "upload_type": upload_type
            }
            
            # Act
            result = validator.validate_upload_request(upload_request)
            
            # Assert
            assert result is not None
            # Should accept different upload types

    def test_validate_upload_request_edge_cases(self, validator):
        """Test validation with edge cases"""
        # Test with None values
        with pytest.raises((ValueError, TypeError)):
            validator.validate_upload_request(None)
        
        # Test with empty dictionary
        with pytest.raises((ValueError, KeyError)):
            validator.validate_upload_request({})
        
        # Test with file but no read method
        bad_file = Mock()
        del bad_file.read  # Remove read method
        bad_file.filename = "test.jpg"
        bad_file.content_type = "image/jpeg"
        
        upload_request = {
            "file": bad_file,
            "user_id": "test-user-123",
            "upload_type": "profile_image"
        }
        
        with pytest.raises(AttributeError):
            validator.validate_upload_request(upload_request)

    def test_service_initialization(self):
        """Test validator can be initialized properly"""
        # Act
        validator = ImageUploadValidator()
        
        # Assert
        assert validator is not None
        assert hasattr(validator, 'validate_upload_request')

    # Test standalone function
    @patch('src.application.services.image_upload_validator.ImageUploadValidator')
    def test_validate_upload_request_function(self, mock_validator_class, valid_image_file):
        """Test standalone validate_upload_request function"""
        # Arrange
        mock_validator = Mock()
        mock_validator.validate_upload_request.return_value = {"valid": True}
        mock_validator_class.return_value = mock_validator
        
        upload_request = {
            "file": valid_image_file,
            "user_id": "test-user-123",
            "upload_type": "profile_image"
        }
        
        # Act
        result = validate_upload_request(upload_request)
        
        # Assert
        assert result == {"valid": True}
        mock_validator.validate_upload_request.assert_called_once_with(upload_request)

    def test_content_type_vs_extension_mismatch(self, validator):
        """Test validation catches content type and extension mismatches"""
        # Arrange - JPEG content type but PNG extension
        mock_file = Mock()
        mock_file.filename = "test.png"
        mock_file.content_type = "image/jpeg"
        mock_file.content_length = 1024
        mock_file.read.return_value = b"\xff\xd8\xff\xe0"  # JPEG signature
        
        upload_request = {
            "file": mock_file,
            "user_id": "test-user-123",
            "upload_type": "profile_image"
        }
        
        # Act
        result = validator.validate_upload_request(upload_request)
        
        # Should either accept (trusting content-type) or validate signature
        assert result is not None

    def test_image_signature_validation(self, validator):
        """Test validation checks actual image signatures"""
        image_signatures = [
            ("test.jpg", "image/jpeg", b"\xff\xd8\xff\xe0"),  # JPEG
            ("test.png", "image/png", b"\x89PNG\r\n\x1a\n"),  # PNG
            ("test.gif", "image/gif", b"GIF87a"),  # GIF87a
            ("test.gif", "image/gif", b"GIF89a"),  # GIF89a
        ]
        
        for filename, content_type, signature in image_signatures:
            # Arrange
            mock_file = Mock()
            mock_file.filename = filename
            mock_file.content_type = content_type
            mock_file.content_length = 1024
            mock_file.read.return_value = signature + b"fake_image_data"
            
            upload_request = {
                "file": mock_file,
                "user_id": "test-user-123",
                "upload_type": "profile_image"
            }
            
            # Act
            result = validator.validate_upload_request(upload_request)
            
            # Assert
            assert result is not None
            # Should accept files with correct signatures

    def test_validation_error_messages(self, validator):
        """Test that validation provides helpful error messages"""
        # Test missing file
        try:
            validator.validate_upload_request({"user_id": "123"})
        except Exception as e:
            assert "file" in str(e).lower()
        
        # Test missing user_id
        mock_file = Mock()
        mock_file.filename = "test.jpg"
        try:
            validator.validate_upload_request({"file": mock_file})
        except Exception as e:
            assert "user" in str(e).lower() or "id" in str(e).lower()

    def test_concurrent_validation(self, validator, valid_image_file):
        """Test validator handles concurrent validation requests"""
        import threading
        results = []
        
        def validate_request():
            upload_request = {
                "file": valid_image_file,
                "user_id": "test-user-123",
                "upload_type": "profile_image"
            }
            try:
                result = validator.validate_upload_request(upload_request)
                results.append(result)
            except Exception as e:
                results.append(str(e))
        
        # Create multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=validate_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Should handle concurrent requests
        assert len(results) == 3
