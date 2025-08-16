from src.infrastructure.db.base import db
from datetime import datetime, timezone

user_favorite_recipes = db.Table('user_favorite_recipes',
    db.Column('user_uid', db.String(128), db.ForeignKey('users.uid'), primary_key=True),
    db.Column('recipe_uid', db.String(36), db.ForeignKey('recipes.uid'), primary_key=True),
    db.Column('favorited_at', db.DateTime, default=datetime.now(timezone.utc))
)
