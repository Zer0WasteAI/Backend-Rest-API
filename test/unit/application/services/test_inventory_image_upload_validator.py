"""
Unit tests for Inventory Image Upload Validator
Tests security and validation for inventory image uploads
"""
import pytest
from unittest.mock import Mock, patch
import io

from src.application.services.inventory_image_upload_validator import (
    InventoryImageUploadValidator,
    validate_inventory_upload
)


class TestInventoryImageUploadValidator:
    """Test suite for Inventory Image Upload Validator"""
    
    @pytest.fixture
    def validator(self):
        """Create inventory image upload validator instance"""
        return InventoryImageUploadValidator()
    
    @pytest.fixture
    def valid_inventory_image(self):
        """Create a valid inventory image file"""
        mock_file = Mock()
        mock_file.filename = "pantry_photo.jpg"
        mock_file.content_type = "image/jpeg"
        mock_file.read.return_value = b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"inventory_image_data"
        mock_file.stream = io.BytesIO(b"inventory_image_data")
        mock_file.seek = Mock()
        mock_file.tell = Mock(return_value=1024)  # 1KB file
        return mock_file

    def test_validate_inventory_upload_success(self, validator, valid_inventory_image):
        """Test successful validation of inventory upload"""
        # Act - should not raise exception
        validator.validate_inventory_upload(valid_inventory_image, "recognition", "test_item")

    def test_validate_inventory_upload_recognition_without_item_name(self, validator, valid_inventory_image):
        """Test validation for recognition uploads without item name"""
        # Act - recognition uploads don't require item_name
        validator.validate_inventory_upload(valid_inventory_image, "recognition")

    def test_validate_inventory_upload_invalid_upload_type(self, validator, valid_inventory_image):
        """Test validation with invalid upload type"""
        # Act & Assert
        with pytest.raises(Exception):
            validator.validate_inventory_upload(valid_inventory_image, "invalid_type", "test_item")

    def test_validate_inventory_upload_no_file(self, validator):
        """Test validation with no file"""
        # Act & Assert
        with pytest.raises(Exception):
            validator.validate_inventory_upload(None, "recognition")

    def test_validate_inventory_upload_empty_filename(self, validator):
        """Test validation with empty filename"""
        # Arrange
        empty_file = Mock()
        empty_file.filename = ""
        
        # Act & Assert
        with pytest.raises(Exception):
            validator.validate_inventory_upload(empty_file, "recognition")

    def test_validate_inventory_upload_invalid_extension(self, validator):
        """Test validation with invalid file extension"""
        # Arrange
        invalid_file = Mock()
        invalid_file.filename = "document.pdf"
        invalid_file.seek = Mock()
        invalid_file.tell = Mock(return_value=1024)
        
        # Act & Assert
        with pytest.raises(Exception):
            validator.validate_inventory_upload(invalid_file, "recognition")

    def test_validate_inventory_upload_oversized_file(self, validator):
        """Test validation with oversized file"""
        # Arrange
        oversized_file = Mock()
        oversized_file.filename = "huge.jpg"
        oversized_file.seek = Mock()
        oversized_file.tell = Mock(return_value=50 * 1024 * 1024)  # 50MB
        
        # Act & Assert
        with pytest.raises(Exception):
            validator.validate_inventory_upload(oversized_file, "recognition")

    def test_validate_inventory_upload_valid_extensions(self, validator):
        """Test validation with all valid extensions"""
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        
        for ext in valid_extensions:
            # Arrange
            valid_file = Mock()
            valid_file.filename = f"test{ext}"
            valid_file.seek = Mock()
            valid_file.tell = Mock(return_value=1024)
            
            # Act - should not raise exception
            validator.validate_inventory_upload(valid_file, "recognition")

    def test_validate_inventory_upload_valid_upload_types(self, validator, valid_inventory_image):
        """Test validation with all valid upload types"""
        valid_types = ['recognition', 'ingredient', 'food']
        
        for upload_type in valid_types:
            # Act - should not raise exception
            validator.validate_inventory_upload(valid_inventory_image, upload_type, "test_item")

    def test_validate_inventory_upload_item_name_validation(self, validator, valid_inventory_image):
        """Test item name validation rules"""
        # Test empty item name when required
        with pytest.raises(Exception):
            validator.validate_inventory_upload(valid_inventory_image, "ingredient", "")
        
        # Test None item name when required  
        with pytest.raises(Exception):
            validator.validate_inventory_upload(valid_inventory_image, "ingredient", None)
        
        # Test too short item name
        with pytest.raises(Exception):
            validator.validate_inventory_upload(valid_inventory_image, "ingredient", "a")
        
        # Test too long item name
        long_name = "x" * 101  # Over MAX_ITEM_NAME_LENGTH
        with pytest.raises(Exception):
            validator.validate_inventory_upload(valid_inventory_image, "ingredient", long_name)
        
        # Test valid item name
        validator.validate_inventory_upload(valid_inventory_image, "ingredient", "valid_item")

    def test_validate_inventory_upload_whitespace_item_name(self, validator, valid_inventory_image):
        """Test item name with whitespace handling"""
        # Test whitespace-only item name
        with pytest.raises(Exception):
            validator.validate_inventory_upload(valid_inventory_image, "ingredient", "   ")
        
        # Test valid item name with leading/trailing whitespace (should be trimmed)
        validator.validate_inventory_upload(valid_inventory_image, "ingredient", "  valid_item  ")

    def test_validation_constants(self, validator):
        """Test validator constants are properly defined"""
        # Assert
        assert hasattr(validator, 'ALLOWED_EXTENSIONS')
        assert hasattr(validator, 'MAX_FILE_SIZE')
        assert hasattr(validator, 'ALLOWED_UPLOAD_TYPES')
        assert hasattr(validator, 'MIN_ITEM_NAME_LENGTH')
        assert hasattr(validator, 'MAX_ITEM_NAME_LENGTH')
        
        # Verify values
        assert validator.MIN_ITEM_NAME_LENGTH == 2
        assert validator.MAX_ITEM_NAME_LENGTH == 100
        assert validator.MAX_FILE_SIZE == 10 * 1024 * 1024  # 10MB
        assert len(validator.ALLOWED_EXTENSIONS) > 0
        assert len(validator.ALLOWED_UPLOAD_TYPES) == 3

    # Test standalone function
    @patch('src.application.services.inventory_image_upload_validator.InventoryImageUploadValidator')
    def test_validate_inventory_upload_function(self, mock_validator_class, valid_inventory_image):
        """Test standalone validate_inventory_upload function"""
        # Arrange
        mock_validator = Mock()
        mock_validator.validate_inventory_upload.return_value = None
        mock_validator_class.return_value = mock_validator
        
        # Act
        result = validate_inventory_upload(valid_inventory_image, "recognition", "test_item")
        
        # Assert
        mock_validator.validate_inventory_upload.assert_called_once_with(
            valid_inventory_image, "recognition", "test_item"
        )

    def test_validator_initialization(self):
        """Test validator can be initialized properly"""
        # Act
        validator = InventoryImageUploadValidator()
        
        # Assert
        assert validator is not None
        assert hasattr(validator, 'validate_inventory_upload')
        assert hasattr(validator, 'ALLOWED_EXTENSIONS')
        assert hasattr(validator, 'MAX_FILE_SIZE')
