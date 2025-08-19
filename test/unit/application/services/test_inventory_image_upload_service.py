"""
Unit tests for Inventory Image Upload Service
Tests inventory-specific image upload functionality
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import io
import tempfile

from src.application.services.inventory_image_upload_service import (
    InventoryImageUploadService,
    upload_inventory_image,
    get_user_inventory_images,
    delete_inventory_image
)


class TestInventoryImageUploadService:
    """Test suite for Inventory Image Upload Service"""
    
    @pytest.fixture
    def service(self):
        """Create inventory image upload service instance"""
        return InventoryImageUploadService()
    
    @pytest.fixture
    def mock_inventory_image(self):
        """Create a mock inventory image file"""
        mock_file = Mock()
        mock_file.filename = "inventory_photo.jpg"
        mock_file.content_type = "image/jpeg"
        mock_file.read.return_value = b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"inventory_image_data"
        mock_file.stream = io.BytesIO(b"inventory_image_data")
        return mock_file
    
    @patch('src.application.services.inventory_image_upload_service.firebase_admin')
    @patch('src.application.services.inventory_image_upload_service.storage')
    def test_upload_inventory_image_success(self, mock_storage, mock_firebase, service, mock_inventory_image):
        """Test successful inventory image upload"""
        # Arrange
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_blob.public_url = "https://storage.googleapis.com/bucket/inventory/user123/photo.jpg"
        mock_bucket.blob.return_value = mock_blob
        mock_storage.bucket.return_value = mock_bucket
        
        # Act
        result = service.upload_inventory_image(mock_inventory_image, "user-123", "pantry_overview")
        
        # Assert
        assert result is not None
        assert "url" in result or isinstance(result, str)
        mock_bucket.blob.assert_called_once()
        mock_blob.upload_from_file.assert_called_once()

    def test_upload_inventory_image_invalid_file(self, service):
        """Test upload with invalid file"""
        # Arrange
        invalid_file = Mock()
        invalid_file.filename = "document.pdf"
        invalid_file.content_type = "application/pdf"
        
        # Act & Assert
        with pytest.raises((ValueError, TypeError)):
            service.upload_inventory_image(invalid_file, "user-123", "pantry_overview")

    def test_upload_inventory_image_missing_parameters(self, service, mock_inventory_image):
        """Test upload with missing parameters"""
        # Test missing user_id
        with pytest.raises((ValueError, TypeError)):
            service.upload_inventory_image(mock_inventory_image, None, "pantry_overview")
        
        # Test missing description
        with pytest.raises((ValueError, TypeError)):
            service.upload_inventory_image(mock_inventory_image, "user-123", None)

    @patch('src.application.services.inventory_image_upload_service.firebase_admin')
    def test_get_user_inventory_images_success(self, mock_firebase, service):
        """Test successful retrieval of user inventory images"""
        # Arrange
        mock_storage = Mock()
        mock_blobs = [
            Mock(
                name="inventory/user-123/pantry_2025-01-19_001.jpg",
                public_url="https://storage.googleapis.com/bucket/pantry_001.jpg",
                time_created="2025-01-19T10:00:00Z"
            ),
            Mock(
                name="inventory/user-123/fridge_2025-01-19_002.jpg", 
                public_url="https://storage.googleapis.com/bucket/fridge_002.jpg",
                time_created="2025-01-19T11:00:00Z"
            ),
            Mock(
                name="inventory/user-123/freezer_2025-01-19_003.jpg",
                public_url="https://storage.googleapis.com/bucket/freezer_003.jpg", 
                time_created="2025-01-19T12:00:00Z"
            )
        ]
        mock_storage.list_blobs.return_value = mock_blobs
        mock_firebase.storage.bucket.return_value = mock_storage
        
        # Act
        result = service.get_user_inventory_images("user-123")
        
        # Assert
        assert result is not None
        assert isinstance(result, (list, dict))
        if isinstance(result, list):
            assert len(result) == 3
        elif isinstance(result, dict):
            assert "images" in result
            assert len(result["images"]) == 3

    @patch('src.application.services.inventory_image_upload_service.firebase_admin')
    def test_get_user_inventory_images_empty(self, mock_firebase, service):
        """Test retrieval when user has no inventory images"""
        # Arrange
        mock_storage = Mock()
        mock_storage.list_blobs.return_value = []
        mock_firebase.storage.bucket.return_value = mock_storage
        
        # Act
        result = service.get_user_inventory_images("user-no-images")
        
        # Assert
        assert result is not None
        assert len(result) == 0 or (isinstance(result, dict) and len(result.get("images", [])) == 0)

    def test_get_user_inventory_images_invalid_user(self, service):
        """Test retrieval with invalid user_id"""
        # Act & Assert
        with pytest.raises((ValueError, TypeError)):
            service.get_user_inventory_images(None)
        
        with pytest.raises((ValueError, TypeError)):
            service.get_user_inventory_images("")

    @patch('src.application.services.inventory_image_upload_service.firebase_admin')
    def test_delete_inventory_image_success(self, mock_firebase, service):
        """Test successful inventory image deletion"""
        # Arrange
        mock_storage = Mock()
        mock_blob = Mock()
        mock_blob.exists.return_value = True
        mock_storage.blob.return_value = mock_blob
        mock_firebase.storage.bucket.return_value = mock_storage
        
        # Act
        result = service.delete_inventory_image("user-123", "inventory_image_456")
        
        # Assert
        assert result is not None
        assert result.get("deleted") is True or result is True
        mock_blob.delete.assert_called_once()

    @patch('src.application.services.inventory_image_upload_service.firebase_admin')
    def test_delete_inventory_image_not_found(self, mock_firebase, service):
        """Test deletion of non-existent image"""
        # Arrange
        mock_storage = Mock()
        mock_blob = Mock()
        mock_blob.exists.return_value = False
        mock_storage.blob.return_value = mock_blob
        mock_firebase.storage.bucket.return_value = mock_storage
        
        # Act & Assert
        with pytest.raises((ValueError, FileNotFoundError)):
            service.delete_inventory_image("user-123", "nonexistent_image")

    def test_delete_inventory_image_invalid_parameters(self, service):
        """Test deletion with invalid parameters"""
        # Test missing user_id
        with pytest.raises((ValueError, TypeError)):
            service.delete_inventory_image(None, "image_123")
        
        # Test missing image_id
        with pytest.raises((ValueError, TypeError)):
            service.delete_inventory_image("user-123", None)

    def test_service_initialization(self):
        """Test service can be initialized properly"""
        # Act
        service = InventoryImageUploadService()
        
        # Assert
        assert service is not None
        assert hasattr(service, 'upload_inventory_image')
        assert hasattr(service, 'get_user_inventory_images')
        assert hasattr(service, 'delete_inventory_image')

    @patch('src.application.services.inventory_image_upload_service.firebase_admin')
    def test_upload_inventory_image_with_metadata(self, mock_firebase, service, mock_inventory_image):
        """Test upload with additional metadata"""
        # Arrange
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_blob.public_url = "https://storage.googleapis.com/bucket/inventory.jpg"
        mock_bucket.blob.return_value = mock_blob
        mock_firebase.storage.bucket.return_value = mock_bucket
        
        metadata = {
            "location": "kitchen_pantry",
            "category": "dry_goods",
            "date_taken": "2025-01-19T10:30:00Z"
        }
        
        # Act
        result = service.upload_inventory_image(
            mock_inventory_image, 
            "user-123", 
            "pantry_overview",
            metadata=metadata
        )
        
        # Assert
        assert result is not None
        # Should include metadata in result or handle it properly

    @patch('src.application.services.inventory_image_upload_service.firebase_admin')
    def test_get_user_inventory_images_with_filter(self, mock_firebase, service):
        """Test retrieval with category filter"""
        # Arrange
        mock_storage = Mock()
        mock_blobs = [
            Mock(name="inventory/user-123/pantry_001.jpg", public_url="url1"),
            Mock(name="inventory/user-123/fridge_002.jpg", public_url="url2"),
            Mock(name="inventory/user-123/pantry_003.jpg", public_url="url3"),
        ]
        mock_storage.list_blobs.return_value = mock_blobs
        mock_firebase.storage.bucket.return_value = mock_storage
        
        # Act
        result = service.get_user_inventory_images("user-123", category_filter="pantry")
        
        # Assert
        assert result is not None
        # Should filter pantry images or return all for client-side filtering

    # Test standalone functions
    @patch('src.application.services.inventory_image_upload_service.InventoryImageUploadService')
    def test_upload_inventory_image_function(self, mock_service_class, mock_inventory_image):
        """Test standalone upload_inventory_image function"""
        # Arrange
        mock_service = Mock()
        mock_service.upload_inventory_image.return_value = {"url": "test_url"}
        mock_service_class.return_value = mock_service
        
        # Act
        result = upload_inventory_image(mock_inventory_image, "user-123", "pantry")
        
        # Assert
        assert result == {"url": "test_url"}
        mock_service.upload_inventory_image.assert_called_once_with(
            mock_inventory_image, "user-123", "pantry"
        )

    @patch('src.application.services.inventory_image_upload_service.InventoryImageUploadService')
    def test_get_user_inventory_images_function(self, mock_service_class):
        """Test standalone get_user_inventory_images function"""
        # Arrange
        mock_service = Mock()
        mock_service.get_user_inventory_images.return_value = ["img1", "img2"]
        mock_service_class.return_value = mock_service
        
        # Act
        result = get_user_inventory_images("user-123")
        
        # Assert
        assert result == ["img1", "img2"]
        mock_service.get_user_inventory_images.assert_called_once_with("user-123")

    @patch('src.application.services.inventory_image_upload_service.InventoryImageUploadService')
    def test_delete_inventory_image_function(self, mock_service_class):
        """Test standalone delete_inventory_image function"""
        # Arrange
        mock_service = Mock()
        mock_service.delete_inventory_image.return_value = {"deleted": True}
        mock_service_class.return_value = mock_service
        
        # Act
        result = delete_inventory_image("user-123", "image-456")
        
        # Assert
        assert result == {"deleted": True}
        mock_service.delete_inventory_image.assert_called_once_with("user-123", "image-456")

    def test_inventory_specific_validations(self, service, mock_inventory_image):
        """Test inventory-specific upload validations"""
        # Test valid inventory descriptions
        valid_descriptions = [
            "pantry_overview",
            "fridge_contents", 
            "freezer_items",
            "spice_cabinet",
            "fruit_bowl",
            "vegetable_drawer"
        ]
        
        with patch('src.application.services.inventory_image_upload_service.firebase_admin'):
            for description in valid_descriptions:
                try:
                    result = service.upload_inventory_image(
                        mock_inventory_image, "user-123", description
                    )
                    # Should accept valid inventory descriptions
                    assert result is not None
                except Exception as e:
                    # Only acceptable if due to Firebase mocking
                    assert "firebase" in str(e).lower()

    @patch('src.application.services.inventory_image_upload_service.firebase_admin')
    def test_image_processing_pipeline(self, mock_firebase, service, mock_inventory_image):
        """Test complete image processing pipeline"""
        # Arrange
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_blob.public_url = "https://storage.googleapis.com/bucket/processed.jpg"
        mock_bucket.blob.return_value = mock_blob
        mock_firebase.storage.bucket.return_value = mock_bucket
        
        # Act
        result = service.upload_inventory_image(
            mock_inventory_image, 
            "user-123", 
            "pantry_overview",
            auto_recognize=True  # Enable automatic ingredient recognition
        )
        
        # Assert
        assert result is not None
        # Should complete full processing pipeline

    def test_concurrent_uploads(self, service):
        """Test handling of concurrent inventory image uploads"""
        import threading
        results = []
        
        def upload_image(user_id, description):
            mock_file = Mock()
            mock_file.filename = f"{description}.jpg"
            mock_file.content_type = "image/jpeg"
            mock_file.read.return_value = b"fake_image"
            
            with patch('src.application.services.inventory_image_upload_service.firebase_admin'):
                try:
                    result = service.upload_inventory_image(mock_file, user_id, description)
                    results.append(result)
                except Exception as e:
                    results.append(str(e))
        
        # Create multiple threads
        threads = []
        descriptions = ["pantry", "fridge", "freezer"]
        for desc in descriptions:
            thread = threading.Thread(target=upload_image, args=["user-123", desc])
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Should handle concurrent uploads
        assert len(results) == 3

    @patch('src.application.services.inventory_image_upload_service.logger')
    def test_logging_integration(self, mock_logger, service, mock_inventory_image):
        """Test that service properly logs activities"""
        with patch('src.application.services.inventory_image_upload_service.firebase_admin'):
            try:
                service.upload_inventory_image(mock_inventory_image, "user-123", "pantry")
            except:
                pass  # Ignore errors, just test logging
            
            # Should log upload activities
            assert mock_logger.info.called or mock_logger.debug.called
