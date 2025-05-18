from typing import List
from src.domain.models.image_reference import ImageReference

class SearchSimilarImagesUseCase:
    def __init__(self, image_repository):
        self.image_repository = image_repository

    def execute(self, similar_name: str)-> List[ImageReference]:
        return self.image_repository.find_by_name_similarity(similar_name)