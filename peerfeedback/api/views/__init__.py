from flask import Blueprint
from flask_restful import Api

from peerfeedback.api.resource import (
    TaskResource,
    FeedbackResource,
    PairingResource,
    AssignSettingsResource,
    NotificationResource,
    MetaFeedbackResource,
    CommentResource,
    CommentLikeResource,
    ExtraFeedbackResource,
)

api_blueprint = Blueprint("api", __name__, url_prefix="/api")

rest_api = Api(api_blueprint)

rest_api.add_resource(TaskResource, "/task/", "/task/<int:task_id>/")
rest_api.add_resource(FeedbackResource, "/feedback/", "/feedback/<int:feed_id>/")
rest_api.add_resource(PairingResource, "/pairing/", "/pairing/<int:pairing_id>/")
rest_api.add_resource(
    AssignSettingsResource,
    "/assignment/settings/",
    "/assignment/settings/<int:settings_id>/",
)
rest_api.add_resource(
    NotificationResource, "/notifications/", "/notification/<int:id>/"
)
rest_api.add_resource(
    MetaFeedbackResource, "/feedback/meta/", "/feedback/meta/<int:meta_id>/"
)
rest_api.add_resource(CommentResource, "/comment/", "/comment/<int:comment_id>/")
rest_api.add_resource(
    CommentLikeResource, "/comment/like/", "/comment/like/<int:like_id>/"
)
rest_api.add_resource(
    ExtraFeedbackResource, "/extra_feedback/", "/extra_feedback/<int:extra_id>/"
)

from .all import *
from .canvas import *
from .pairing import *
from .feedback import *
from .rubric import *
from .exports import *
from .email import *
from .task import *
from .jobs import *
from .ml import *
from .analytics import *
