from datetime import datetime
from typing import Optional, List

class Generation:
    def __init__(
        self,
        uid: str,
        user_uid: str,
        generated_at: datetime,
        raw_result: dict,
        generation_type: str,  # "inventory" o "custom"
        recipes_ids: Optional[List[str]] = None,
        is_validated: bool = False,
        validated_at: Optional[datetime] = None
    ):
        self.uid = uid
        self.user_uid = user_uid
        self.generated_at = generated_at
        self.raw_result = raw_result
        self.generation_type = generation_type
        self.recipes_ids = recipes_ids
        self.is_validated = is_validated
        self.validated_at = validated_at

    def __repr__(self):
        return (
            f"<Generation(uid={self.uid}, user_uid={self.user_uid}, "
            f"generated_at={self.generated_at}, generation_type={self.generation_type}, "
            f"is_validated={self.is_validated})>"
        )
