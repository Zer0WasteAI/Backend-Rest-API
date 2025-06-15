from abc import ABC, abstractmethod
from typing import List, Optional
from src.domain.models.generation import Generation

class GenerationRepository(ABC):
    @abstractmethod
    def save(self, generation: Generation) -> str:
        pass

    @abstractmethod
    def find_by_user(self, user_uid: str) -> List[Generation]:
        pass

    @abstractmethod
    def find_by_uid(self, generation_uid: str) -> Optional[Generation]:
        pass

    @abstractmethod
    def update_validation_status(self, generation_uid: str, validated: bool) -> None:
        pass
