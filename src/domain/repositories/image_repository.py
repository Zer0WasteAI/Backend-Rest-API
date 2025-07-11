from abc import ABC, abstractmethod
from typing import Optional
from src.domain.models.image_reference import ImageReference

class ImageReferenceRepository(ABC):
    @abstractmethod
    def save(self, image: ImageReference) -> str:
        pass

    @abstractmethod
    def find_by_uid(self, uid: str) -> Optional[ImageReference]:
        pass

    @abstractmethod
    def find_by_name(self, name: str) -> Optional[ImageReference]:
        pass

    @abstractmethod
    def find_best_match_name(self, name_query: str) -> Optional[ImageReference]:
        pass
