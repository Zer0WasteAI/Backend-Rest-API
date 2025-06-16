from abc import ABC, abstractmethod
from typing import List, Optional
from src.domain.models.environmental_savings import EnvironmentalSavings

class EnvironmentalSavingsRepository(ABC):
    @abstractmethod
    def save(self, savings: EnvironmentalSavings) -> Optional[EnvironmentalSavings]:
        pass

    @abstractmethod
    def find_by_user(self, user_uid: str) -> List[EnvironmentalSavings]:
        pass
    @abstractmethod
    def find_by_uid(self, saving_uid: str) -> Optional[EnvironmentalSavings]:
        pass

    @abstractmethod
    def update_type_status(self, saving_uid: str, is_cooked: bool) -> None:
        pass

    @abstractmethod
    def find_by_user_and_by_is_cooked(self, user_uid: str, is_cooked: bool) -> List[EnvironmentalSavings]:
        pass
