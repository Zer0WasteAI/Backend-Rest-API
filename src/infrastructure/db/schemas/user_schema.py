from datetime import datetime, timezone
from src.infrastructure.db.base import db
from src.infrastructure.db.models.user_favorite_recipes import user_favorite_recipes


class User(db.Model):
    __tablename__ = "users"
    uid = db.Column(db.String(128), primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    favorite_recipes = db.relationship(
        'RecipeORM',
        secondary=user_favorite_recipes,
        back_populates='favorited_by',
        lazy='dynamic'
    )

User.auth = db.relationship("AuthUser", backref="user", uselist=False)
User.profile = db.relationship("ProfileUser", backref="user", uselist=False)