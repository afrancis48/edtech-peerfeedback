from marshmallow import Schema
from marshmallow.fields import Boolean, DateTime, Float, Integer, Nested, String, Url
from peerfeedback.extensions import marsh
from peerfeedback.models import (
    AssignmentSettings,
    Comment,
    CommentLike,
    CourseUserMap,
    ExtraFeedback,
    Feedback,
    Medal,
    MetaFeedback,
    Notification,
    Pairing,
    Rubric,
    RubricCriteria,
    Task,
)


class TermSchema(Schema):
    name = String()
    end_at = String()


class EnrollmentSchema(Schema):
    enrollment_state = String()
    role = String()
    type = String()
    user_id = Integer()


class CourseSchema(Schema):
    id = Integer()
    name = String()
    public_description = String()
    workflow_state = String()
    term = Nested(TermSchema)
    enrollments = Nested(EnrollmentSchema, many=True)
    end_at = String()
    image_download_url = Url()


class AssignmentSchema(Schema):
    id = Integer()
    name = String()
    description = String()
    due_at = String()
    course_id = Integer()
    group_category_id = Integer()
    intra_group_peer_reviews = Boolean()


class SubmissionSchema(Schema):
    id = Integer()
    assignment_id = Integer()
    assignment = Nested(AssignmentSchema)
    course = Nested(CourseSchema)
    body = String()
    submission_type = String()
    url = Url()
    workflow_state = String()


class UserSchema(marsh.Schema):
    class Meta:
        datetimeformat = "%Y-%m-%dT%H:%M:%S+00:00"

    id = Integer()
    name = String()
    avatar_url = Url()
    reputation = Float()
    feedback_given = Integer()
    oldest_review = DateTime()


class FullUserSchema(UserSchema):
    real_name = String()


class PairingSchema(marsh.ModelSchema):
    class Meta:
        model = Pairing
        datetimeformat = "%Y-%m-%dT%H:%M:%S+00:00"

    grader = marsh.Nested(UserSchema)
    recipient = marsh.Nested(UserSchema)
    creator = marsh.Nested(UserSchema)


class MetaFeedbackSchema(marsh.ModelSchema):
    class Meta:
        model = MetaFeedback
        datetimeformat = "%Y-%m-%dT%H:%M:%S+00:00"

    feedback_id = Integer()
    receiver_id = Integer()
    reviewer_id = Integer()


class FeedbackSchema(marsh.ModelSchema):
    class Meta:
        model = Feedback
        datetimeformat = "%Y-%m-%dT%H:%M:%S+00:00"

    rubric_id = Integer()
    reviewer = marsh.Nested(UserSchema)
    receiver = marsh.Nested(UserSchema)
    rating = marsh.Nested(MetaFeedbackSchema)


class TaskSchema(marsh.ModelSchema):
    class Meta:
        model = Task
        datetimeformat = "%Y-%m-%dT%H:%M:%S+00:00"


class NotificationSchema(marsh.ModelSchema):
    class Meta:
        model = Notification
        datetimeformat = "%Y-%m-%dT%H:%M:%S+00:00"

    user_id = Integer()
    notifier = marsh.Nested(UserSchema)
    user = marsh.Nested(UserSchema)


class RubricCriteriaSchema(marsh.ModelSchema):
    class Meta:
        model = RubricCriteria
        datetimeformat = "%Y-%m-%dT%H:%M:%S+00:00"


class RubricSchema(marsh.ModelSchema):
    class Meta:
        model = Rubric
        datetimeformat = "%Y-%m-%dT%H:%M:%S+00:00"

    owner_id = Integer()
    owner = marsh.Nested(UserSchema)
    criterions = marsh.Nested(RubricCriteriaSchema, many=True)


class AssignmentSettingsSchema(marsh.ModelSchema):
    class Meta:
        model = AssignmentSettings
        datetimeformat = "%Y-%m-%dT%H:%M:%S+00:00"

    rubric_id = Integer()


class CommentLikeSchema(marsh.ModelSchema):
    class Meta:
        model = CommentLike
        datetimeformat = "%Y-%m-%dT%H:%M:%S+00:00"

    user = marsh.Nested(UserSchema)


class CommentSchema(marsh.ModelSchema):
    class Meta:
        model = Comment
        datetimeformat = "%Y-%m-%dT%H:%M:%S+00:00"

    likes = marsh.Nested(CommentLikeSchema, many=True)
    commenter = marsh.Nested(UserSchema)


class ExtraFeedbackSchema(marsh.ModelSchema):
    class Meta:
        model = ExtraFeedback
        datetimeformat = "%Y-%m-%dT%H:%M:%S+00:00"

    user = marsh.Nested(UserSchema)


class MedalSchema(marsh.ModelSchema):
    class Meta:
        model = Medal
        datetimeformat = "%Y-%m-%dT%H:%M:%S+00:00"


class CourseUserMapSchema(marsh.ModelSchema):
    class Meta:
        model = CourseUserMap
        datetimeformat = "%Y-%m-%dT%H:%M:%S+00:00"


class TaskWithPairing(TaskSchema):
    pairing = marsh.Nested(PairingSchema, exclude=("pseudo_name", "study"))


class PairingWithTask(PairingSchema):
    task = marsh.Nested(TaskSchema)


class RealPairingSchema(marsh.ModelSchema):
    class Meta:
        model = Pairing
        datetimeformat = "%Y-%m-%dT%H:%M:%S+00:00"

    grader = marsh.Nested(FullUserSchema)
    recipient = marsh.Nested(FullUserSchema)
    creator = marsh.Nested(FullUserSchema)
    task = marsh.Nested(TaskSchema)


task_schema = TaskSchema()
task_with_pairing = TaskWithPairing()
full_feedback = FeedbackSchema()
feedback_schema = FeedbackSchema(exclude=["rating", "read_time", "write_time"])
feedback_with_rating = FeedbackSchema(exclude=["read_time", "write_time"])
pairing_schema = PairingSchema(exclude=["feedback", "task", "pseudo_name", "study"])
pairing_with_task = PairingWithTask(exclude=["feedback", "pseudo_name", "study"])
asettings_schema = AssignmentSettingsSchema()
notification_schema = NotificationSchema()
meta_feedback_schema = MetaFeedbackSchema()
comment_schema = CommentSchema()
like_schema = CommentLikeSchema()
extra_feedback_schema = ExtraFeedbackSchema()
user_schema = UserSchema()
real_user_schema = FullUserSchema()
medal_schema = MedalSchema()
real_pairing = RealPairingSchema()
rubric_schema = RubricSchema(exclude=["criterions"])
full_rubric = RubricSchema()
