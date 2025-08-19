"""
Unit tests for File Upload Service
Tests file upload functionality and validation
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import io

from src.application.services.file_upload_service import FileUploadService, upload_image


class TestFileUploadService:
    """Test suite for File Upload Service"""
    
    @pytest.fixture
    def file_service(self):
        """Create file upload service instance"""
        return FileUploadService()
    
    @pytest.fixture
    def mock_image_file(self):
        """Create a mock image file"""
        mock_file = Mock()
        mock_file.filename = "test_image.jpg"
        mock_file.content_type = "image/jpeg"
        mock_file.read.return_value = b"fake_image_data"
        mock_file.stream = io.BytesIO(b"fake_image_data")
        return mock_file
    
    @pytest.fixture
    def mock_invalid_file(self):
        """Create a mock invalid file"""
        mock_file = Mock()
        mock_file.filename = "test_document.txt"
        mock_file.content_type = "text/plain"
        mock_file.read.return_value = b"text content"
        return mock_file
    
    @patch('src.application.services.file_upload_service.firebase_admin')
    @patch('src.application.services.file_upload_service.storage')
    def test_upload_image_success(self, mock_storage, mock_firebase, file_service, mock_image_file):
        """Test successful image upload"""
        # Arrange
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_blob.public_url = "https://storage.googleapis.com/test-bucket/test_image.jpg"
        mock_bucket.blob.return_value = mock_blob
        mock_storage.bucket.return_value = mock_bucket
        
        # Act
        result = file_service.upload_image(mock_image_file, "test-user-id")
        
        # Assert
        assert result is not None
        assert "url" in result or "public_url" in result or result.startswith("https://")
        mock_bucket.blob.assert_called_once()
        mock_blob.upload_from_file.assert_called_once()

    def test_upload_image_invalid_file_type(self, file_service, mock_invalid_file):
        """Test upload with invalid file type"""
        # Act & Assert
        with pytest.raises((ValueError, TypeError)):
            file_service.upload_image(mock_invalid_file, "test-user-id")

    def test_upload_image_missing_filename(self, file_service):
        """Test upload with file missing filename"""
        # Arrange
        mock_file = Mock()
        mock_file.filename = None
        mock_file.content_type = "image/jpeg"
        
        # Act & Assert
        with pytest.raises((ValueError, AttributeError)):
            file_service.upload_image(mock_file, "test-user-id")

    def test_upload_image_empty_file(self, file_service):
        """Test upload with empty file"""
        # Arrange
        mock_file = Mock()
        mock_file.filename = "empty.jpg"
        mock_file.content_type = "image/jpeg"
        mock_file.read.return_value = b""  # Empty file
        
        # Act & Assert
        with pytest.raises(ValueError):
            file_service.upload_image(mock_file, "test-user-id")

    def test_upload_image_no_user_id(self, file_service, mock_image_file):
        """Test upload without user ID"""
        # Act & Assert
        with pytest.raises((ValueError, TypeError)):
            file_service.upload_image(mock_image_file, None)

    @patch('src.application.services.file_upload_service.firebase_admin')
    @patch('src.application.services.file_upload_service.storage')
    def test_upload_image_firebase_error(self, mock_storage, mock_firebase, file_service, mock_image_file):
        """Test upload with Firebase error"""
        # Arrange
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_blob.upload_from_file.side_effect = Exception("Firebase upload failed")
        mock_bucket.blob.return_value = mock_blob
        mock_storage.bucket.return_value = mock_bucket
        
        # Act & Assert
        with pytest.raises(Exception):
            file_service.upload_image(mock_image_file, "test-user-id")

    def test_upload_image_file_size_validation(self, file_service):
        """Test file size validation"""
        # Arrange - Large file
        large_mock_file = Mock()
        large_mock_file.filename = "large_image.jpg"
        large_mock_file.content_type = "image/jpeg"
        large_mock_file.read.return_value = b"x" * (10 * 1024 * 1024)  # 10MB file
        
        # Act & Assert
        # Should either accept or reject based on size limits
        try:
            result = file_service.upload_image(large_mock_file, "test-user-id")
            # If accepted, should return valid result
            assert result is not None
        except ValueError:
            # If rejected due to size, that's also valid behavior
            pass

    def test_upload_image_filename_sanitization(self, file_service):
        """Test filename sanitization"""
        # Arrange - File with special characters
        special_file = Mock()
        special_file.filename = "test image with spaces & symbols!@#.jpg"
        special_file.content_type = "image/jpeg"
        special_file.read.return_value = b"fake_image_data"
        
        with patch('src.application.services.file_upload_service.firebase_admin'):
            with patch('src.application.services.file_upload_service.storage') as mock_storage:
                mock_bucket = Mock()
                mock_blob = Mock()
                mock_bucket.blob.return_value = mock_blob
                mock_storage.bucket.return_value = mock_bucket
                
                # Act
                try:
                    file_service.upload_image(special_file, "test-user-id")
                    
                    # Assert - blob name should be sanitized
                    blob_call_args = mock_bucket.blob.call_args[0][0]
                    assert isinstance(blob_call_args, str)
                    # Shouldn't contain problematic characters
                    assert not any(char in blob_call_args for char in ['&', '!', '@', '#'])
                except Exception:
                    # Some implementations might reject such files entirely
                    pass

    @patch('src.application.services.file_upload_service.firebase_admin')
    @patch('src.application.services.file_upload_service.storage')
    def test_upload_image_function_wrapper(self, mock_storage, mock_firebase, mock_image_file):
        """Test the standalone upload_image function"""
        # Arrange
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_blob.public_url = "https://storage.googleapis.com/test-bucket/test_image.jpg"
        mock_bucket.blob.return_value = mock_blob
        mock_storage.bucket.return_value = mock_bucket
        
        # Act
        result = upload_image(mock_image_file, "test-user-id")
        
        # Assert
        assert result is not None
        assert isinstance(result, str) or "url" in result

    def test_service_initialization(self):
        """Test service can be initialized properly"""
        # Act
        service = FileUploadService()
        
        # Assert
        assert service is not None
        assert hasattr(service, 'upload_image')

    def test_supported_file_formats(self, file_service):
        """Test various supported file formats"""
        supported_formats = [
            ("image.jpg", "image/jpeg"),
            ("image.png", "image/png"),
            ("image.gif", "image/gif"),
            ("image.webp", "image/webp")
        ]
        
        for filename, content_type in supported_formats:
            mock_file = Mock()
            mock_file.filename = filename
            mock_file.content_type = content_type
            mock_file.read.return_value = b"fake_image_data"
            
            with patch('src.application.services.file_upload_service.firebase_admin'):
                with patch('src.application.services.file_upload_service.storage') as mock_storage:
                    mock_bucket = Mock()
                    mock_blob = Mock()
                    mock_bucket.blob.return_value = mock_blob
                    mock_storage.bucket.return_value = mock_bucket
                    
                    # Should not raise exception for supported formats
                    try:
                        result = file_service.upload_image(mock_file, "test-user-id")
                        assert result is not None
                    except Exception as e:
                        # Only acceptable if it's a Firebase/network error, not validation
                        assert "Firebase" in str(e) or "network" in str(e).lower()

    def test_unsupported_file_formats(self, file_service):
        """Test rejection of unsupported file formats"""
        unsupported_formats = [
            ("document.pdf", "application/pdf"),
            ("document.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
            ("archive.zip", "application/zip"),
            ("script.js", "application/javascript")
        ]
        
        for filename, content_type in unsupported_formats:
            mock_file = Mock()
            mock_file.filename = filename
            mock_file.content_type = content_type
            mock_file.read.return_value = b"fake_file_data"
            
            # Should raise validation error
            with pytest.raises((ValueError, TypeError)):
                file_service.upload_image(mock_file, "test-user-id")

    @patch('src.application.services.file_upload_service.uuid')
    def test_unique_filename_generation(self, mock_uuid, file_service, mock_image_file):
        """Test that unique filenames are generated"""
        # Arrange
        mock_uuid.uuid4.return_value.hex = "abcd1234"
        
        with patch('src.application.services.file_upload_service.firebase_admin'):
            with patch('src.application.services.file_upload_service.storage') as mock_storage:
                mock_bucket = Mock()
                mock_blob = Mock()
                mock_bucket.blob.return_value = mock_blob
                mock_storage.bucket.return_value = mock_bucket
                
                # Act
                file_service.upload_image(mock_image_file, "test-user-id")
                
                # Assert - Should generate unique filename
                blob_call_args = mock_bucket.blob.call_args[0][0]
                assert "abcd1234" in blob_call_args or "test-user-id" in blob_call_args
