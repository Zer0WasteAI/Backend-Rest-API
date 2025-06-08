class DeleteUserRecipeUseCase:
    def __init__(self, recipe_repository):
        self.recipe_repository = recipe_repository

    def execute(self, user_uid: str, title: str) -> None:
        return self.recipe_repository.delete_by_user_and_title(user_uid, title)