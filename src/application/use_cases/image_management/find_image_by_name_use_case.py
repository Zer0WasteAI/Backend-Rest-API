from typing import Optional
from src.domain.models.image_reference import ImageReference

class FindImageByNameUseCase:
    def __init__(self, image_repository):
        self.image_repository = image_repository

    def execute(self, name: str) -> Optional[ImageReference]:
        return self.image_repository.find_by_name(name)

