from flask_login import UserMixin
from sqlalchemy.orm import backref, validates

from peerfeedback.database import SurrogatePK, Model, TimeData, Column, relationship
from peerfeedback.extensions import db


class User(UserMixin, SurrogatePK, Model, TimeData):
    """A user of the app."""

    __tablename__ = "users"
    avatar_url = Column(db.Text)
    bio = Column(db.Text)
    canvas_access_token = Column(db.Text)
    canvas_expiration_time = Column(db.DateTime(timezone=True))
    canvas_id = Column(db.Integer, nullable=False)
    canvas_refresh_token = Column(db.Text)
    email = Column(db.String(80), unique=True, nullable=False)
    name = Column(db.String(100), nullable=False)
    real_name = Column(db.String(100), nullable=False)
    username = Column(db.String(80), unique=True, nullable=False)
    feedback_given = Column(db.Integer)
    reputation = Column(db.Float)
    oldest_review = Column(db.DateTime)

    settings = relationship(
        "UserSettings", uselist=False, cascade="all,delete", back_populates="user"
    )

    def __init__(self, canvas_id, username, email, **kwargs):
        """Create instance."""
        db.Model.__init__(
            self, canvas_id=canvas_id, username=username, email=email, **kwargs
        )

    def __repr__(self):
        """Represent instance as a unique string."""
        return "<User ({username!r})>".format(username=self.username)

    def as_dict(self):
        return dict(
            id=self.id,
            name=self.name,
            email=self.email,
            canvas_id=self.canvas_id,
            username=self.username,
            avatar_url=self.avatar_url,
        )


class JWTToken(Model):
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False)
    token_type = db.Column(db.String(10), nullable=False)
    user_identity = db.Column(db.String(80), nullable=False)
    revoked = db.Column(db.Boolean, nullable=False)
    expires = db.Column(db.DateTime, nullable=False)

    def to_dict(self):
        return {
            "token_id": self.id,
            "jti": self.jti,
            "token_type": self.token_type,
            "user_identity": self.user_identity,
            "revoked": self.revoked,
            "expires": self.expires,
        }

    def __repr__(self):
        return "<JWTToken ({jti})>".format(jti=self.jti)


class UserSettings(SurrogatePK, Model):
    __tablename__ = "user_settings"

    comment_emails = Column(db.Boolean, default=True)
    feedback_emails = Column(db.Boolean, default=True)
    discussion_emails = Column(db.Boolean, default=True)
    # Applicable only to teachers and TA's
    pairing_emails = Column(db.Boolean, server_default="t")
    submission_warning = Column(db.Boolean, server_default="t", default=True)

    user_id = db.Column(
        db.ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE")
    )
    user = db.relationship("User", back_populates="settings")

    def __repr__(self):
        return "<UserSettings {0} for user {1}>".format(self.id, self.user_id)


class Pairing(TimeData, SurrogatePK, Model):
    """Model storing information about the grader and recipient of a feedback"""

    __tablename__ = "pairing"

    STUDENT = "student"
    TA = "TA"
    IGR = "igr"  # intra group review
    types = (STUDENT, TA, IGR)

    # type of pairing is either student or TA
    type = Column(db.String(10))
    course_id = Column(db.Integer, nullable=False)
    assignment_id = Column(db.Integer, nullable=False)
    pseudo_name = Column(db.String(150))
    archived = Column(db.Boolean, server_default="f", default=False)
    view_only = Column(db.Boolean, default=False)

    grader_id = Column(
        db.ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    recipient_id = Column(
        db.ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    creator_id = Column(
        db.ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    study_id = Column(
        db.ForeignKey("study.id", onupdate="CASCADE", ondelete="SET NULL")
    )
    grader = db.relationship("User", foreign_keys=[grader_id])
    recipient = db.relationship("User", foreign_keys=[recipient_id])
    creator = db.relationship("User", foreign_keys=[creator_id])
    study = db.relationship("Study", backref=backref("pairings", lazy="select"))

    def __repr__(self):
        return f"<Pairing {self.id} ({self.grader_id}=>{self.recipient_id})>"


class Feedback(TimeData, SurrogatePK, Model):
    """Feedback provided by the grader for an assignment"""

    __tablename__ = "feedback"

    STUDENT = "student"
    TA = "TA"
    IGR = "igr"  # intra group review
    TYPES = (STUDENT, TA, IGR)

    # feedback types like grading, review, marks ..etc.,
    type = Column(db.String(15))
    value = Column(db.Text)
    grades = Column(db.JSON)
    ml_rating = Column(db.Integer)
    ml_prob = Column(db.Float)
    draft = Column(db.Boolean)
    submission_id = Column(db.Integer)
    assignment_name = Column(db.String(150))
    assignment_id = Column(db.Integer)
    course_name = Column(db.String(150))
    course_id = Column(db.Integer)
    # Date and Time when the user started writing the feedback
    start_date = Column(db.DateTime)
    # Date and Time when the user submitted the feedback
    end_date = Column(db.DateTime)
    # Time (in sec) spent by the user reading the pdf
    read_time = Column(db.Integer)
    # Time (in sec) spent filling in the rubric and writing the feedback
    write_time = Column(db.Integer)
    receiver_id = Column(
        db.ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE")
    )
    reviewer_id = Column(
        db.ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE")
    )
    pairing_id = Column(
        db.ForeignKey("pairing.id", onupdate="CASCADE", ondelete="CASCADE")
    )
    rubric_id = Column(
        db.ForeignKey("rubric.id", onupdate="CASCADE", ondelete="SET NULL")
    )

    pairing = db.relationship(
        "Pairing",
        backref=backref("feedback", uselist=False, cascade="all,delete"),
        lazy=True,
    )
    rubric = db.relationship("Rubric")
    reviewer = db.relationship(
        "User", backref="feedbacks", foreign_keys=[reviewer_id], lazy=True
    )
    receiver = db.relationship("User", foreign_keys=[receiver_id], lazy=True)

    def __repr__(self):
        return f"<Feedback {self.id} for submission {self.submission_id}>"

    @validates("grades")
    def validate_grades(self, key, grades):
        try:
            assert isinstance(grades, list)
            for item in grades:
                assert isinstance(item, dict)
                assert "criteria" in item and "level" in item
                assert isinstance(item["criteria"], str)
                assert isinstance(item["level"], int) or item["level"] is None
        except AssertionError:
            raise AssertionError(
                "Invalid formatting for grades. Should be an array of objects "
                "in the format [{criteria: name<str>, level: id<int>}, ...]"
            )
        return grades


class Task(TimeData, SurrogatePK, Model):
    """Information about the assignment to give Feedback.

    course_id, assignment_id and and user_id are required to retrieve a
    submission using the CANVAS API

    The names are stored to make it easier to show the task in UI
    """

    __tablename__ = "task"

    PENDING = "PENDING"
    IN_PROGRESS = "INPROGRESS"
    COMPLETE = "COMPLETE"
    ARCHIVED = "ARCHIVED"
    states = (PENDING, IN_PROGRESS, COMPLETE, ARCHIVED)

    status = Column(db.String(10))  # one of the `states`
    course_id = Column(db.Integer)
    course_name = Column(db.String(150))
    assignment_id = Column(db.Integer)
    assignment_name = Column(db.String(150))
    start_date = Column(db.DateTime)
    due_date = Column(db.DateTime)
    done_date = Column(db.DateTime)
    view_only = Column(db.Boolean, nullable=True, default=False)

    user_id = Column(db.ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"))
    pairing_id = Column(
        db.ForeignKey("pairing.id", onupdate="CASCADE", ondelete="CASCADE")
    )

    user = db.relationship("User", backref="tasks")
    pairing = db.relationship(
        "Pairing", backref=backref("task", uselist=False, cascade="all,delete")
    )

    def __repr__(self):
        return f"<Task {self.id} of user {self.user_id}>"


class Notification(TimeData, SurrogatePK, Model):
    """Task to track any feedback/comment left by users on an assignment.

    Notifications follow the template of
        ```
        <Notifier Name> has left a <feedback/comment/reply> on <user>'s assignment
        <Assignment Name> in course <Course Name>
        ```
    """

    __tablename__ = "notification"

    FEEDBACK = "feedback"
    COMMENT = "comment"
    LIKE = "like"
    MEDAL = "medal"
    items = (FEEDBACK, COMMENT, LIKE, MEDAL)

    read = Column(db.Boolean, default=False)
    item = Column(db.String(15))  # one of the `items`
    item_id = Column(db.Integer)
    course_name = Column(db.String(150))
    course_id = Column(db.Integer)
    assignment_name = Column(db.String(150))
    assignment_id = Column(db.Integer)

    # ID of the submission user
    user_id = Column(db.ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"))
    # ID of the user receiving the notification
    recipient_id = Column(
        db.ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE")
    )
    # ID of the user generating the notification
    notifier_id = Column(
        db.ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE")
    )

    user = db.relationship("User", foreign_keys=[user_id])
    recipient = db.relationship(
        "User", backref="notifications", foreign_keys=[recipient_id]
    )
    notifier = db.relationship("User", foreign_keys=[notifier_id])

    def __repr__(self):
        return f"<Notification {self.id} for user {self.recipient_id}>"


class Rubric(TimeData, SurrogatePK, Model):
    """Evaluation Rubric"""

    __tablename__ = "rubric"

    name = Column(db.String(100), nullable=False)
    description = Column(db.Text)
    public = Column(db.Boolean, default=True)
    active = Column(db.Boolean, default=True)
    owner_id = Column(
        db.ForeignKey("users.id", onupdate="CASCADE", ondelete="SET NULL")
    )

    owner = db.relationship("User", backref="rubrics", lazy=True)

    def __repr__(self):
        return f"<Rubric {self.id}: {self.name}>"


class RubricCriteria(SurrogatePK, Model):
    """Strands in a rubric"""

    __tablename__ = "rubric_criteria"

    name = Column(db.String(100), nullable=False)
    description = Column(db.Text)
    levels = Column(db.JSON)
    rubric_id = Column(
        db.ForeignKey("rubric.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )

    rubric = db.relationship("Rubric", backref="criterions", lazy=True)

    def __repr__(self):
        return f"<RubricCriteria {self.id} of Rubric {self.rubric_id}>"

    @validates("levels")
    def validate_levels(self, key, levels):
        try:
            assert isinstance(levels, list)
            for item in levels:
                assert isinstance(item, dict)
                assert "position" in item and "text" in item and "points" in item
                assert isinstance(item["position"], int)
                assert isinstance(item["text"], str)
                assert isinstance(item["points"], int) or isinstance(
                    item["points"], float
                )
        except AssertionError:
            raise AssertionError("Invalid formatting of criteria levels.")

        if not len(levels):
            raise AssertionError("Criteria should have at least 1 level of grades")

        return levels


class AssignmentSettings(TimeData, SurrogatePK, Model):
    """Application specific settings for the assignments"""

    __tablename__ = "assignment_settings"

    course_id = Column(db.Integer, nullable=False)
    assignment_id = Column(db.Integer, nullable=False, unique=True)
    allow_student_pairing = Column(db.Boolean, default=False)
    allow_view_peer_assignments = Column(db.Boolean, default=False)
    feedback_suggestion = Column(db.String, default="")
    # max_reviews is a misleading. It's NOT a count of the maximum number of
    # reviews a student will be giving. It counts the maximum EXTRA reviews
    # that students can give by creating pairs themselves when the value
    # `allow_student_pairing` is set to True
    max_reviews = Column(db.Integer)
    use_rubric = Column(db.Boolean)
    rubric_id = Column(
        db.ForeignKey("rubric.id", onupdate="CASCADE", ondelete="SET NULL"),
        nullable=True,
    )
    feedback_deadline = Column(db.Integer)
    custom_deadline = Column(db.DateTime)
    deadline_format = Column(db.String(10), server_default="canvas")
    filter_pdf = Column(db.Boolean, server_default="f")
    intra_group_review = Column(db.Boolean, server_default="f", default=False)

    rubric = db.relationship("Rubric", backref="assignments", lazy=True)

    def __repr__(self):
        return f"<AssignmentSettings {self.id} for {self.assignment_id}>"


class MetaFeedback(TimeData, SurrogatePK, Model):
    """Ratings for feedback left by peers on an assignment"""

    __tablename__ = "meta_feedback"

    points = Column(db.Integer)
    comment = Column(db.Text)

    feedback_id = Column(
        db.ForeignKey("feedback.id", onupdate="CASCADE", ondelete="CASCADE")
    )
    receiver_id = Column(
        db.ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE")
    )
    reviewer_id = Column(
        db.ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE")
    )

    feedback = db.relationship(
        "Feedback", backref=backref("rating", uselist=False), lazy=True
    )
    receiver = db.relationship("User", foreign_keys=[receiver_id], lazy=True)
    reviewer = db.relationship("User", foreign_keys=[reviewer_id], lazy=True)

    def __repr__(self):
        return f"<MetaFeedback {self.id}>"

    @validates("points")
    def validate_points(self, key, points):
        if 0 <= points < 7:
            return points
        raise ValueError("Points should be in the range 0 to 6")


class Comment(TimeData, SurrogatePK, Model):
    """Comments on assignments left by different people"""

    __tablename__ = "comment"

    value = Column(db.Text)
    course_id = Column(db.Integer)
    course_name = Column(db.String)
    assignment_id = Column(db.Integer)
    assignment_name = Column(db.String)
    submission_id = Column(db.Integer)

    recipient_id = Column(
        db.ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE")
    )
    commenter_id = Column(
        db.ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE")
    )
    recipient = db.relationship("User", foreign_keys=[recipient_id], lazy=True)
    commenter = db.relationship("User", foreign_keys=[commenter_id], lazy=True)

    def __repr__(self):
        return f"<Comment {self.id}>"

    @validates("value")
    def validate_value(self, key, value):
        if len(value.strip()):
            return value
        raise AssertionError("Cannot save empty comment")


class CommentLike(TimeData, SurrogatePK, Model):
    """Likes on comments"""

    __tablename__ = "comment_like"

    user_id = Column(db.ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"))
    comment_id = Column(
        db.ForeignKey("comment.id", onupdate="CASCADE", ondelete="CASCADE")
    )

    user = db.relationship("User", backref=backref("likes"))
    comment = db.relationship("Comment", backref=backref("likes"))

    def __repr__(self):
        return f"<CommentLike {self.id} on comment {self.comment_id}>"


class ExtraFeedback(TimeData, SurrogatePK, Model):
    """Requests for extra feedback on assignments from peers"""

    __tablename__ = "extra_feedback"

    active = Column(db.Boolean)
    course_id = Column(db.Integer)
    assignment_id = Column(db.Integer)
    user_id = Column(db.ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"))

    user = db.relationship("User", backref="extra_feedbacks")

    def __repr__(self):
        return f"<ExtraFeedback {self.id} by {self.user_id}>"


class Medal(TimeData, SurrogatePK, Model):
    """Medals given to the users when certain thresholds are crossed"""

    __tablename__ = "medal"

    name = Column(db.String(50))
    user_id = Column(db.ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"))
    user = db.relationship("User", backref="medals")

    def __repr__(self):
        return f"<Medal {self.id}: {self.name} of user {self.user_id}>"


class CourseUserMap(TimeData, SurrogatePK, Model):
    """Map of users and the courses they are associated with and their roles"""

    __tablename__ = "course_usermap"

    STUDENT = "student"
    TA = "ta"
    TEACHER = "teacher"
    ROLES = (STUDENT, TA, TEACHER)

    course_id = Column(db.Integer)
    role = Column(db.String(20))
    user_id = Column(db.ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"))

    user = db.relationship("User", backref="courses")

    def __repr__(self):
        return f"<CourseUserMap {self.id} of {self.user_id}>"

    @staticmethod
    def role_of(enrollment):
        map = {
            "StudentEnrollment": CourseUserMap.STUDENT,
            "TaEnrollment": CourseUserMap.TA,
            "TeacherEnrollment": CourseUserMap.TEACHER,
        }
        return map[enrollment] if enrollment in map.keys() else None


study_user_associations = db.Table(
    "study_user_association",
    Column("study_id", db.Integer, db.ForeignKey("study.id")),
    Column("user_id", db.Integer, db.ForeignKey("users.id")),
)


class Study(TimeData, SurrogatePK, Model):
    """Model for Studies that are conducted on the platform"""

    __tablename__ = "study"

    name = Column(db.String(150))
    start_date = Column(db.DateTime)
    end_date = Column(db.DateTime)

    # A CSV list of Assignment IDs that will be a part of the study
    assignments = Column(db.Text)

    participants = db.relationship(
        "User",
        secondary=study_user_associations,
        backref=backref("studies", lazy="select"),
    )
