from marshmallow import Schema, fields, validate

class CustomRecipeRequestSchema(Schema):
    ingredients = fields.List(fields.String(), required=True, validate=validate.Length(min=1))
    preferences = fields.List(fields.String(), missing=[])
    num_recipes = fields.Integer(missing=2, validate=validate.Range(min=1, max=5))

class SaveRecipeRequestSchema(Schema):
    title = fields.String(required=True, validate=validate.Length(min=1, max=200))
    duration = fields.String(required=True)
    difficulty = fields.String(required=True, validate=validate.OneOf(["Fácil", "Intermedio", "Difícil"]))
    ingredients = fields.List(fields.String(), required=True, validate=validate.Length(min=1))
    steps = fields.List(fields.String(), required=True, validate=validate.Length(min=1))
    footer = fields.String(missing="")
    is_custom = fields.Boolean(missing=False)

class RecipeSchema(Schema):
    uid = fields.String(required=True)
    title = fields.String(required=True)
    duration = fields.String(required=True)
    difficulty = fields.String(required=True)
    ingredients = fields.List(fields.String(), required=True)
    steps = fields.List(fields.String(), required=True)
    footer = fields.String(allow_none=True)
    is_custom = fields.Boolean(required=True)
    saved_at = fields.DateTime(required=True) 