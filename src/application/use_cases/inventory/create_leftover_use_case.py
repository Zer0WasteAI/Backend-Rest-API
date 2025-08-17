from datetime import date, datetime
from src.domain.models.leftover_item import LeftoverItem
from src.domain.models.ingredient_batch import StorageLocation
from src.infrastructure.db.leftover_repository_impl import LeftoverRepository
from src.shared.exceptions.custom import InvalidRequestDataException
import uuid

class CreateLeftoverUseCase:
    def __init__(self, leftover_repository: LeftoverRepository):
        self.leftover_repository = leftover_repository

    def execute(
        self,
        recipe_uid: str,
        title: str,
        portions: int,
        eat_by: str,
        storage_location: str,
        user_uid: str,
        session_id: str = None
    ) -> dict:
        """
        Create a leftover item from cooking session.
        
        Args:
            recipe_uid: UID of the original recipe
            title: Title for the leftover (e.g., "Ají de gallina (sobras)")
            portions: Number of portions left
            eat_by: Date when leftover should be consumed by (ISO date)
            storage_location: Where the leftover is stored
            user_uid: UID of the user
            session_id: Optional cooking session that created this leftover
            
        Returns:
            Dict with leftover info and planner suggestion
        """
        # Validate inputs
        if portions <= 0:
            raise InvalidRequestDataException(details={"portions": "Must be positive"})
        
        try:
            eat_by_date = datetime.fromisoformat(eat_by).date()
        except ValueError:
            raise InvalidRequestDataException(details={"eat_by": "Invalid date format"})
        
        try:
            storage = StorageLocation(storage_location)
        except ValueError:
            raise InvalidRequestDataException(details={"storage_location": "Invalid storage location"})
        
        # Validate eat_by is in the future
        if eat_by_date <= date.today():
            raise InvalidRequestDataException(details={"eat_by": "Must be a future date"})
        
        # Create leftover
        leftover = LeftoverItem(
            leftover_id=str(uuid.uuid4()),
            recipe_uid=recipe_uid,
            user_uid=user_uid,
            title=title,
            portions=portions,
            eat_by=eat_by_date,
            storage_location=storage,
            session_id=session_id
        )
        
        # Save leftover
        saved_leftover = self.leftover_repository.save(leftover)
        
        # Generate planner suggestion
        planner_suggestion = saved_leftover.generate_planner_suggestion()
        
        return {
            "leftover_id": saved_leftover.leftover_id,
            "title": saved_leftover.title,
            "portions": saved_leftover.portions,
            "eat_by": saved_leftover.eat_by.isoformat(),
            "storage_location": saved_leftover.storage_location.value,
            "created_at": saved_leftover.created_at.isoformat(),
            "planner_suggestion": planner_suggestion
        }