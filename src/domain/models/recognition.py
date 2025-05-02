from datetime import datetime
from typing import Optional, List

class Recognition:
    def __init__(
            self,
            uid: str,
            user_uid: str,
            recognized_at: datetime,
            raw_result: dict,
            is_validated: bool = False,
            validated_at: Optional[datetime] = None,
            image_path: Optional[str] = None,
            images_paths: Optional[List[str]] = None
                 ):
        self.uid = uid
        self.user_uid = user_uid
        self.image_path = image_path
        self.recognized_at = recognized_at
        self.raw_result = raw_result
        self.is_validated = is_validated
        self.validated_at = validated_at
        self.images_paths = images_paths

def __repr__(self):
    return (
        f"<Recognition(uid={self.uid}, user_uid={self.user_uid}, "
        f"image_path='{self.image_path}', recognized_at={self.recognized_at}, "
        f"is_validated={self.is_validated})', 'image_path={self.images_paths}'>"
    )