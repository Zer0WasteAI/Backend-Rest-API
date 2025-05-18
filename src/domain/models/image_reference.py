from typing import List, Optional

class ImageReference:
    def __init__(
        self,
        uid: str,
        name: str,
        image_path: str,
        image_type: str
    ):
        self.uid = uid
        self.name = name.lower()
        self.image_path = image_path
        self.image_type = image_type

    def __repr__(self):
        return f"<ImageReference(uid={self.uid}, name={self.name}, type={self.type}, image_path={self.image_path})>"
