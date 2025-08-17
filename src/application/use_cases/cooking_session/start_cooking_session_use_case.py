from datetime import datetime
from src.domain.models.cooking_session import CookingSession, CookingLevel, CookingStep
from src.infrastructure.db.cooking_session_repository_impl import CookingSessionRepository
from src.infrastructure.db.recipe_repository_impl import RecipeRepositoryImpl
from src.shared.exceptions.custom import RecipeNotFoundException
import uuid

class StartCookingSessionUseCase:
    def __init__(
        self,
        cooking_session_repository: CookingSessionRepository,
        recipe_repository: RecipeRepositoryImpl
    ):
        self.cooking_session_repository = cooking_session_repository
        self.recipe_repository = recipe_repository

    def execute(
        self,
        recipe_uid: str,
        servings: int,
        level: str,
        user_uid: str,
        started_at: datetime
    ) -> CookingSession:
        """
        Start a new cooking session.
        
        Args:
            recipe_uid: UID of the recipe to cook
            servings: Number of servings to prepare
            level: Cooking level (beginner|intermediate|advanced)
            user_uid: UID of the user
            started_at: When the session started
            
        Returns:
            CookingSession object
            
        Raises:
            RecipeNotFoundException: If recipe is not found
            ValueError: For invalid inputs
        """
        # Validate inputs
        if servings <= 0:
            raise ValueError("Servings must be positive")
        
        try:
            cooking_level = CookingLevel(level)
        except ValueError:
            raise ValueError(f"Invalid cooking level: {level}")
        
        # Verify recipe exists
        recipe = self.recipe_repository.find_by_uid(recipe_uid)
        if not recipe:
            raise RecipeNotFoundException(f"Recipe with UID {recipe_uid} not found")
        
        # Check for existing active sessions
        active_sessions = self.cooking_session_repository.find_active_sessions(user_uid)
        if len(active_sessions) >= 3:  # Limit concurrent sessions
            raise ValueError("Too many active cooking sessions. Please finish existing sessions first.")
        
        # Create new cooking session
        session_id = str(uuid.uuid4())
        
        cooking_session = CookingSession(
            session_id=session_id,
            recipe_uid=recipe_uid,
            user_uid=user_uid,
            servings=servings,
            level=cooking_level,
            started_at=started_at
        )
        
        # Initialize steps based on recipe
        if hasattr(recipe, 'steps') and recipe.steps:
            for i, recipe_step in enumerate(recipe.steps):
                cooking_step = CookingStep(step_id=f"S{i+1}")
                cooking_session.add_step(cooking_step)
        
        # Save session
        saved_session = self.cooking_session_repository.save(cooking_session)
        
        return saved_session