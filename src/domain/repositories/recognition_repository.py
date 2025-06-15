from abc import ABC, abstractmethod
from typing import List, Optional
from src.domain.models.recognition import Recognition

class RecognitionRepository(ABC):
    @abstractmethod
    def save(self, recognition: Recognition) -> str:
        pass

    @abstractmethod
    def find_by_user(self, user_uid: str) -> List[Recognition]:
        pass

    @abstractmethod
    def find_by_uid(self, recognition_uid: str) -> Optional[Recognition]:
        pass

    @abstractmethod
    def update_validation_status(self, recognition_uid: str, validated: bool) -> None:
        pass