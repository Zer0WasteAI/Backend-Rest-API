from datetime import datetime
from typing import List, Optional

class Recipe:
    def __init__(
        self,
        uid: str,
        user_uid: str,
        title: str,
        duration: str,
        difficulty: str,
        ingredients: List[str],
        steps: List[str],
        footer: str,
        is_custom: bool = False,
        saved_at: Optional[datetime] = None
    ):
        self.uid = uid
        self.user_uid = user_uid
        self.title = title
        self.duration = duration
        self.difficulty = difficulty
        self.ingredients = ingredients
        self.steps = steps
        self.footer = footer
        self.is_custom = is_custom
        self.saved_at = saved_at or datetime.now()

    def __repr__(self):
        return f"Recipe(uid={self.uid}, title={self.title}, user_uid={self.user_uid})" 