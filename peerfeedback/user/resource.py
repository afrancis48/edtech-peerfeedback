from flask_jwt_extended import get_current_user, jwt_required
from flask_restful import Resource, abort, fields, marshal_with, reqparse
from peerfeedback.models import UserSettings

settings_fields = {
    "id": fields.Integer,
    "comment_emails": fields.Boolean,
    "feedback_emails": fields.Boolean,
    "discussion_emails": fields.Boolean,
    "pairing_emails": fields.Boolean,
    "user_id": fields.Integer,
    "submission_warning": fields.Boolean,
}

user_fields = {
    "id": fields.Integer,
    "avatar_url": fields.String,
    "bio": fields.String,
    "canvas_id": fields.Integer,
    "username": fields.String,
    "name": fields.String,
    "email": fields.String,
    "reputation": fields.Float,
    "feedback_given": fields.Integer,
    "oldest_review": fields.DateTime,
}


class UserSettingsResource(Resource):

    method_decorators = [jwt_required]

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("comment_emails", type=bool)
        self.parser.add_argument("feedback_emails", type=bool)
        self.parser.add_argument("discussion_emails", type=bool)
        self.parser.add_argument("pairing_emails", type=bool)
        self.parser.add_argument("submission_warning", type=bool)

    @marshal_with(settings_fields)
    def get(self):
        user = get_current_user()
        settings = UserSettings.query.filter_by(user_id=user.id).first()
        if not settings:
            settings = UserSettings.create(user_id=user.id)
            settings.save()
        return settings

    @marshal_with(settings_fields)
    def put(self):
        user = get_current_user()
        settings = UserSettings.query.filter_by(user_id=user.id).first()

        if not settings:
            abort(404)

        args = self.parser.parse_args()
        args = {k: v for k, v in args.items() if v is not None}
        settings.update(**args)
        return settings

    @marshal_with(settings_fields)
    def post(self):
        user = get_current_user()
        settings = UserSettings.query.filter_by(user_id=user.id).first()

        if settings:
            abort(409)

        args = self.parser.parse_args()
        args = {k: v for k, v in args.items() if v is not None}
        args["user_id"] = user.id
        settings = UserSettings.create(**args)
        return settings, 201


class UserResource(Resource):

    method_decorators = [jwt_required]

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("bio", type=str)
        self.parser.add_argument("name", type=str)
        self.parser.add_argument("email", type=str)

    @marshal_with(user_fields)
    def get(self):
        return get_current_user()

    @marshal_with(user_fields)
    def put(self):
        args = self.parser.parse_args()
        args = {k: v for k, v in args.items() if v is not None}
        user = get_current_user()
        user.update(**args)
        return user
