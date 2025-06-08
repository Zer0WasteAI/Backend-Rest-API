from marshmallow import Schema, fields, validate

class CustomRecipeRequestSchema(Schema):
    ingredients = fields.List(fields.String(), required=True, validate=validate.Length(min=1))
    preferences = fields.List(fields.String(), missing=[])
    num_recipes = fields.Integer(missing=2, validate=validate.Range(min=1, max=5))

from marshmallow import Schema, fields, validate

class RecipeIngredientSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1))
    quantity = fields.Float(required=True)
    type_unit = fields.String(required=True)

class RecipeStepSchema(Schema):
    step_order = fields.Integer(required=True)
    description = fields.String(required=True)

class SaveRecipeRequestSchema(Schema):
    title = fields.String(required=True, validate=validate.Length(min=1, max=200))
    duration = fields.String(required=True)
    difficulty = fields.String(required=True, validate=validate.OneOf(["Fácil", "Intermedio", "Difícil"]))
    ingredients = fields.List(fields.Nested(RecipeIngredientSchema), required=True, validate=validate.Length(min=1))
    steps = fields.List(fields.Nested(RecipeStepSchema), required=True, validate=validate.Length(min=1))
    footer = fields.String(missing="")
    generated_by_ai = fields.Boolean(required=True)

class RecipeSchema(Schema):
    title = fields.String(required=True)
    duration = fields.String(required=True)
    difficulty = fields.String(required=True)
    ingredients = fields.List(fields.Nested(RecipeIngredientSchema), required=True)
    steps = fields.List(fields.Nested(RecipeStepSchema), required=True)
    footer = fields.String(allow_none=True)
    generated_by_ai = fields.Boolean(required=True)
    saved_at = fields.DateTime(required=True)
