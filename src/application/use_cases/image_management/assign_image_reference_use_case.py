from typing import Optional
from src.domain.models.image_reference import ImageReference

class AssignImageReferenceUseCase:
    def __init__(self, image_repository, fallback_name: str = "imagen-defecto") -> None:
        self.image_repository = image_repository
        self.fallback_name = fallback_name

    def execute(self, item_name: str) -> Optional[ImageReference]:
        exact = self.image_repository.find_by_name(item_name)
        if exact:
            return exact

        similars = self.image_repository.find_by_name_similarity(item_name)
        if similars:
            return similars[0]

        return None # Si es none se habilita el usecase generar img
    # El usecase genera la img y la guarda en la db