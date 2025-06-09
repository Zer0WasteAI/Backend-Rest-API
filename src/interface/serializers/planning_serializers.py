from marshmallow import Schema, fields, validate
from .recipe_serializers import SaveRecipeRequestSchema, RecipeSchema

class SaveMealPlanRequestSchema(Schema):
    date = fields.Date(required=True)
    meals = fields.List(fields.Nested(SaveRecipeRequestSchema), required=True, validate=validate.Length(min=1))
class MealPlanSchema(Schema):
    date = fields.Date(required=True)
    breakfast = fields.Nested(RecipeSchema, allow_none=True)
    lunch = fields.Nested(RecipeSchema, allow_none=True)
    dinner = fields.Nested(RecipeSchema, allow_none=True)
    dessert = fields.Nested(RecipeSchema, allow_none=True)