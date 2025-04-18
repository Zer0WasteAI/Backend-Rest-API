from marshmallow import Schema, fields

class OAuthCodeSchema(Schema):
    code = fields.Str(required=True)