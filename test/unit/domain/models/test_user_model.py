"""
Unit tests for User domain model
Tests basic user creation, validation, and behavior
"""
import pytest
from datetime import datetime
from src.domain.models.user import User


class TestUserModel:
    """Test suite for User domain model"""

    def test_user_creation_with_required_fields(self):
        """Test creating a user with only required fields"""
        # Arrange
        uid = "test-uid-123"
        email = "test@example.com"
        
        # Act
        user = User(uid=uid, email=email)
        
        # Assert
        assert user.uid == uid
        assert user.email == email
        assert user.created_at is None  # Default value
        assert user.updated_at is None  # Default value

    def test_user_creation_with_all_fields(self):
        """Test creating a user with all fields provided"""
        # Arrange
        uid = "test-uid-456"
        email = "full@example.com"
        created_at = datetime(2023, 1, 1)
        updated_at = datetime(2023, 1, 2)
        
        # Act
        user = User(
            uid=uid,
            email=email,
            crated_at=created_at,  # Note: typo in original model
            updated_at=updated_at
        )
        
        # Assert
        assert user.uid == uid
        assert user.email == email
        assert user.created_at == created_at
        assert user.updated_at == updated_at

    def test_user_uid_validation(self):
        """Test that user UID is properly assigned"""
        # Arrange
        test_cases = [
            "simple-uid",
            "complex-uid-with-123-numbers",
            "firebase-uid-D1vPwLSM65TLzFtmNqWrlv6gfut1",
            ""  # Empty string should be allowed for now
        ]
        
        # Act & Assert
        for uid in test_cases:
            user = User(uid=uid, email="test@example.com")
            assert user.uid == uid

    def test_user_email_validation(self):
        """Test email field assignment"""
        # Arrange
        test_emails = [
            "simple@example.com",
            "complex.email+tag@domain.co.uk",
            "user@localhost",
            None  # Anonymous users might have None email
        ]
        
        # Act & Assert
        for email in test_emails:
            user = User(uid="test-uid", email=email)
            assert user.email == email

    def test_user_representation(self):
        """Test user string representation"""
        # Arrange
        uid = "test-uid-repr"
        email = "repr@example.com"
        created_at = datetime(2023, 5, 15)
        updated_at = datetime(2023, 5, 16)
        
        user = User(
            uid=uid,
            email=email,
            crated_at=created_at,
            updated_at=updated_at
        )
        
        # Act
        repr_str = repr(user)
        
        # Assert
        assert uid in repr_str
        assert email in repr_str
        assert str(created_at) in repr_str
        assert str(updated_at) in repr_str
        assert repr_str.startswith("User(")

    def test_user_equality_based_on_uid(self):
        """Test if users with same UID are considered equal"""
        # Arrange
        uid = "same-uid"
        user1 = User(uid=uid, email="user1@example.com")
        user2 = User(uid=uid, email="user2@example.com")
        user3 = User(uid="different-uid", email="user1@example.com")
        
        # Act & Assert
        # Note: Current model doesn't implement __eq__, 
        # so this tests object identity, not logical equality
        assert user1 is not user2
        assert user1 is not user3
        
        # UIDs should match
        assert user1.uid == user2.uid
        assert user1.uid != user3.uid

    def test_user_attribute_modification(self):
        """Test that user attributes can be modified after creation"""
        # Arrange
        user = User(uid="test-uid", email="original@example.com")
        new_email = "updated@example.com"
        new_updated_at = datetime.now()
        
        # Act
        user.email = new_email
        user.updated_at = new_updated_at
        
        # Assert
        assert user.email == new_email
        assert user.updated_at == new_updated_at

    @pytest.mark.parametrize("uid,email", [
        ("uid1", "email1@test.com"),
        ("uid2", "email2@test.com"),
        ("firebase-uid", None),
        ("", "anonymous@example.com"),
    ])
    def test_user_creation_parametrized(self, uid, email):
        """Parametrized test for various user creation scenarios"""
        # Act
        user = User(uid=uid, email=email)
        
        # Assert
        assert user.uid == uid
        assert user.email == email

    def test_user_model_typo_in_created_at_parameter(self):
        """Test that the typo in 'crated_at' parameter works as expected"""
        # Note: There's a typo in the original model - 'crated_at' instead of 'created_at'
        # This test documents this behavior
        
        # Arrange
        created_time = datetime(2023, 12, 1)
        
        # Act
        user = User(uid="test", email="test@example.com", crated_at=created_time)
        
        # Assert
        assert user.created_at == created_time  # The attribute is correctly named