from typing import Optional
from src.domain.models.image_reference import ImageReference

class AssignImageReferenceUseCase:
    def __init__(self, image_repository, fallback_name: str = "imagen_defecto") -> None:
        self.image_repository = image_repository
        self.fallback_name = fallback_name

    def execute(self, name: str) -> Optional[ImageReference]:
        exact = self.image_repository.find_by_name(name)
        if exact:
            return exact

        similars = self.image_repository.find_by_name_similarity(name)
        if similars:
            return similars[0]

        return self.image_repository.find_by_name(self.fallback_name)