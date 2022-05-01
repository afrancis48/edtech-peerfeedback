from datetime import datetime, timezone
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from flask import request, current_app as app
from flask_restful import Resource, abort, reqparse
from flask_jwt_extended import jwt_required, get_current_user
from dateutil.parser import parse as parse_date

from peerfeedback.extensions import db
from peerfeedback.api import errors
from peerfeedback.api.jobs.sendmail import (
    send_feedback_notification,
    send_discussion_notification,
)
from peerfeedback.api.jobs.notifications import notify_discussion_participants
from peerfeedback.api.jobs.medals import (
    award_contributor_medal,
    award_super_commentator,
    award_generous_reviewer_medal,
)
from peerfeedback.api.jobs.tasks import update_task_deadline
from peerfeedback.api.jobs.course import import_course_information
from peerfeedback.api.jobs.feedback import (
    reopen_submitted_feedback,
    disable_submitted_feedback_grades,
    change_rubric_on_unsubmitted_feedback,
)
from peerfeedback.models import (
    User,
    Pairing,
    Feedback,
    Task,
    Notification,
    AssignmentSettings,
    MetaFeedback,
    Comment,
    CommentLike,
    ExtraFeedback,
    CourseUserMap,
    Study,
)
from peerfeedback.api.utils import (
    get_canvas_client,
    create_pairing,
    user_is_ta_or_teacher,
    get_course_teacher,
)
from peerfeedback.api.schemas import (
    task_schema,
    feedback_schema,
    pairing_schema,
    asettings_schema,
    notification_schema,
    meta_feedback_schema,
    like_schema,
    comment_schema,
    extra_feedback_schema,
    task_with_pairing,
)


class TaskResource(Resource):
    method_decorators = [jwt_required]

    def __init__(self):
        self.put_parser = reqparse.RequestParser()
        self.parser.add_argument("status", choices=Task.states, required=True)
        self.parser.add_argument("view_only", type=str)

        self.get_parser = reqparse.RequestParser()
        self.get_parser.add_argument("status", choices=Task.states, action="append")
        self.get_parser.add_argument("course_id", type=int, location="args")
        self.get_parser.add_argument("view_only", type=str)
        super(TaskResource, self).__init__()

    def get(self):
        user = get_current_user()
        args = self.get_parser.parse_args()
        query = Task.query.options(
            joinedload(Task.pairing).joinedload(Pairing.recipient)
        ).filter_by(user_id=user.id)
        if args["status"]:
            query = query.filter(Task.status.in_(args["status"]))
        if args["course_id"]:
            query = query.filter(Task.course_id == args["course_id"])
        tasks = query.all()
        task_dicts = []
        for task in tasks:
            task_dict = task_with_pairing.dump(task)
            if task.status != Task.COMPLETE and task.pairing.pseudo_name:
                task_dict["pairing"]["recipient"]["name"] = task.pairing.pseudo_name
                task_dict["pairing"]["recipient"]["avatar_url"] = ""
            task_dicts.append(task_dict)

        return task_dicts

    def put(self, task_id):
        args = self.put_parser.parse_args()
        task = Task.query.get(task_id)
        if not task:
            abort(404)
        task.status = args["status"]
        task.save()
        return task_schema.jsonify(task)


class FeedbackResource(Resource):
    method_decorators = [jwt_required]

    def __init__(self):
        super(FeedbackResource, self).__init__()

    def get(self, feed_id):
        user = get_current_user()
        feedback = (
            Feedback.query.options(joinedload(Feedback.reviewer))
            .options(joinedload(Feedback.receiver))
            .get(feed_id)
        )

        if not feedback:
            abort(404)

        if (
            user.id != feedback.reviewer_id
            and user.id != feedback.receiver_id
            and not user_is_ta_or_teacher(user.id, feedback.course_id)
        ):
            abort(403)

        return feedback_schema.jsonify(feedback)

    def put(self, feed_id):
        user = get_current_user()
        feedback = Feedback.query.get(feed_id)
        if not feedback:
            abort(404, message="Invalid Feedback ID")
        if feedback.reviewer_id != user.id:
            abort(401)
        if not feedback.draft:  # already published
            abort(400, message="Feedback is not a draft. Cannot update.")

        json = request.get_json()
        if "draft" not in json:
            json["draft"] = True

        update_attrs = ["draft", "value", "grades", "write_time", "read_time"]
        try:
            for attr in update_attrs:
                if attr in json:
                    setattr(feedback, attr, json[attr])
        except AssertionError as e:
            abort(400, message=str(e))

        if not json["draft"]:
            non_igr_value_empty = (
                feedback.type != Feedback.IGR
                and "value" in json
                and len(json["value"].strip().split(" ")) < 10
            )
            if non_igr_value_empty:
                abort(400, message="Feedback cannot be less than 10 words.")
            feedback.end_date = datetime.utcnow()

        if not feedback.start_date:
            feedback.start_date = datetime.utcnow()
        feedback.save()

        task = Task.query.filter(Task.pairing_id == feedback.pairing_id).first()
        if task.status == Task.PENDING:
            task.status = Task.IN_PROGRESS
            task.start_date = datetime.utcnow()
            task.save()

        if json["draft"]:
            return feedback_schema.jsonify(feedback)

        task.update(status=Task.COMPLETE, done_date=datetime.utcnow())
        notification = Notification.create(
            item=Notification.FEEDBACK,
            item_id=feedback.id,
            course_name=feedback.course_name,
            course_id=feedback.course_id,
            assignment_name=feedback.assignment_name,
            assignment_id=feedback.assignment_id,
            user_id=feedback.receiver_id,
            notifier_id=user.id,
            recipient_id=feedback.receiver_id,
        )
        if feedback.type == Feedback.IGR:
            notification.notifier_id = None
        notification.save()
        award_contributor_medal.queue(feedback.id)
        award_generous_reviewer_medal.queue(user.id)

        if app.config.get("SEND_NOTIFICATION_EMAILS"):
            send_feedback_notification.queue(feedback.id)

        return feedback_schema.jsonify(feedback)


class PairingResource(Resource):
    method_decorators = [jwt_required]

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("type", type=str)
        self.parser.add_argument("course_id", type=int, required=True)
        self.parser.add_argument("assignment_id", type=int, required=True)
        self.parser.add_argument("recipient_id", type=int, required=True)
        self.parser.add_argument("recipient_name", type=str)
        self.parser.add_argument("view_only", type=str)

        self.put_parser = reqparse.RequestParser()
        self.put_parser.add_argument("archived", type=bool, required=True)

        super(PairingResource, self).__init__()

    def get(self, pairing_id):
        # pull the grader and recipient from the DB
        pairing = (
            Pairing.query.options(joinedload(Pairing.feedback))
            .options(joinedload(Pairing.recipient))
            .options(joinedload(Pairing.grader))
            .get(pairing_id)
        )

        if not pairing:
            abort(404)
        return pairing_schema.jsonify(pairing)

    def post(self):
        args = self.parser.parse_args()
        user = get_current_user()
        if args["view_only"] is None:
            view_only = False
        else:
            view_only = True
        if args["recipient_id"] == user.id:
            abort(400, message=errors.GRADER_RECIPIENT_SAME)

        settings = AssignmentSettings.query.filter(
            AssignmentSettings.assignment_id == args["assignment_id"]
        ).first()
        if not settings:
            abort(400, message=errors.ASSIGNMENT_NOT_SETUP)

        pair_count = (
            db.session.query(func.count(Pairing.id))
                .filter(Pairing.course_id == args["course_id"])
                .filter(Pairing.assignment_id == args["assignment_id"])
                .filter(Pairing.grader_id == user.id)
                .filter(Pairing.creator_id == user.id)
                .scalar()
        )
        if view_only is False and pair_count >= settings.max_reviews:
            abort(400, message=errors.MAX_LIMIT_REACHED)

        if args["type"] != Pairing.TA:
            args["type"] = Pairing.STUDENT


        recipient = User.query.get(args["recipient_id"])
        teacher = get_course_teacher(args["course_id"])
        canvas = get_canvas_client(teacher.canvas_access_token)
        course = canvas.get_course(args["course_id"])
        assignment = course.get_assignment(args["assignment_id"])


        # Make sure that extra pairing happens only after the assignment deadline
        # has passed
        if assignment.due_at:
            due_at = parse_date(assignment.due_at).astimezone(timezone.utc)
            now = datetime.now(timezone.utc)
            if due_at > now:
                abort(400, message=errors.EXTRAS_ONLY_AFTER_DUE)


        submission = assignment.get_submission(recipient.canvas_id)
        if submission.workflow_state == "unsubmitted":
            abort(412, message=errors.ASSIGNMENT_NOT_SUBMITTED)

        # get study if assignment is associated
        studies = Study.query.filter(
            Study.start_date < datetime.now(), Study.end_date > datetime.now()
        )
        active_study = None
        for study in studies:
            if not study.assignments:
                continue
            assignments = study.assignments.split(",")
            if str(assignment.id) in assignments:
                active_study = study
        participants = []
        if active_study:
            participants = [p.id for p in active_study.participants]

        pseudo_name = None
        if user.id in participants and recipient.id in participants:
            pseudo_name = args["recipient_name"]

        try:
            pairing = create_pairing(
                user,
                user,
                recipient,
                course,
                assignment,
                args["type"],
                study=active_study,
                pseudo_name=pseudo_name,
                view_only=view_only
            )
        except errors.PairingToSelf:
            return abort(400, message=errors.GRADER_RECIPIENT_SAME)
        except errors.PairingExists:
            return abort(409, message=errors.PAIRING_EXISTS)

        # deactivate extra feedback request if any
        extra_request = (
            ExtraFeedback.query.filter(ExtraFeedback.course_id == args["course_id"])
                .filter(ExtraFeedback.assignment_id == args["assignment_id"])
                .filter(ExtraFeedback.user_id == args["recipient_id"])
                .filter(ExtraFeedback.active.is_(True))
                .first()
        )

        if extra_request:
            extra_request.active = False
            extra_request.save()

        return pairing_schema.dump(pairing), 201

    def put(self, pairing_id):
        pairing = Pairing.query.get(pairing_id)
        if not pairing:
            return abort(404)

        user = get_current_user()
        if not user_is_ta_or_teacher(user, pairing.course_id):
            return abort(403)

        args = self.put_parser.parse_args()
        archive = args["archived"]
        pairing.archived = archive
        if archive:
            pairing.task.status = Task.ARCHIVED
        else:
            if pairing.task.status == Task.ARCHIVED:
                pairing.task.status = Task.PENDING
        pairing.save()
        return pairing_schema.jsonify(pairing)


class AssignSettingsResource(Resource):
    method_decorators = [jwt_required]

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("course_id", type=int, required=True)
        self.parser.add_argument("assignment_id", type=int, required=True)
        self.parser.add_argument("allow_student_pairing", type=bool)
        self.parser.add_argument("allow_view_peer_assignments", type=bool)
        self.parser.add_argument("feedback_suggestion", type=str)
        self.parser.add_argument("max_reviews", type=int)
        self.parser.add_argument("use_rubric", type=bool)
        self.parser.add_argument("rubric_id", type=int)
        self.parser.add_argument("feedback_deadline", type=int)
        self.parser.add_argument("custom_deadline", type=lambda d: parse_date(d))
        self.parser.add_argument("deadline_format", choices=["canvas", "custom"])
        self.parser.add_argument("on_rubric_change", type=str)
        self.parser.add_argument("filter_pdf", type=bool)
        self.parser.add_argument("intra_group_review", type=bool)
        super(AssignSettingsResource, self).__init__()

    def get(self):
        args = self.parser.parse_args()
        settings_obj = AssignmentSettings.query.filter_by(
            course_id=args["course_id"], assignment_id=args["assignment_id"]
        ).first()

        if not settings_obj:
            abort(404)

        return asettings_schema.jsonify(settings_obj)

    def put(self, settings_id):
        args = self.parser.parse_args()
        user = get_current_user()
        if not user_is_ta_or_teacher(user, args["course_id"]):
            return abort(403)

        settings = AssignmentSettings.query.get(settings_id)
        if not settings:
            return abort(404)

        # remove the on rubric change flag from model args
        on_rubric_change = args["on_rubric_change"]
        del args["on_rubric_change"]

        deadline_changed = (
            settings.feedback_deadline != args["feedback_deadline"]
            or settings.deadline_format != args["deadline_format"]
            or settings.custom_deadline != args["custom_deadline"]
        )
        old_rubric = settings.rubric_id
        if args["rubric_id"] == 0:
            del args["rubric_id"]
        if not args["use_rubric"]:
            args["rubric_id"] = None
        if not args["feedback_suggestion"]:
            args["feedback_suggestion"] = ""

        settings.update(**args)

        if deadline_changed:
            update_task_deadline.queue(settings.assignment_id, user.id)

        if settings.rubric_id != old_rubric:
            change_rubric_on_unsubmitted_feedback.queue(
                settings.assignment_id, settings.rubric_id
            )
            if on_rubric_change == "disable":
                disable_submitted_feedback_grades.queue(
                    settings.assignment_id, old_rubric
                )
            elif on_rubric_change == "reopen":
                emails = app.config.get("SEND_NOTIFICATION_EMAILS")
                reopen_submitted_feedback.queue(
                    settings.assignment_id, settings.rubric_id, emails
                )

        # carry out mapping if not already done by the professor
        mapped = CourseUserMap.query.filter_by(course_id=settings.course_id).all()
        if not mapped:
            import_course_information.queue(args["course_id"], user.id)
        return asettings_schema.jsonify(settings)


class NotificationResource(Resource):
    method_decorators = [jwt_required]

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("read", type=bool, required=True)
        super(NotificationResource, self).__init__()

    def get(self):
        user = get_current_user()
        notes = (
            Notification.query.filter(
                Notification.recipient_id == user.id, Notification.read.is_(False)
            )
            .options(joinedload(Notification.user), joinedload(Notification.notifier))
            .order_by(Notification.id.desc())
            .all()
        )
        return notification_schema.jsonify(notes, many=True)

    def put(self, id):
        args = self.parser.parse_args()
        notification = Notification.query.get(id)
        if not notification:
            abort(404)

        notification.update(**args)
        return notification_schema.jsonify(notification)


class MetaFeedbackResource(Resource):
    method_decorators = [jwt_required]

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("feedback_id", type=int, required=True)
        self.parser.add_argument("points", type=int, required=True)
        self.parser.add_argument("comment", type=str)
        self.parser.add_argument("receiver_id", type=int, required=True)
        super(MetaFeedbackResource, self).__init__()

    def get(self, meta_id):
        rating = MetaFeedback.query.get(meta_id)
        if not rating:
            abort(404)
        return meta_feedback_schema.jsonify(rating)

    def post(self):
        args = self.parser.parse_args()
        args["reviewer_id"] = get_current_user().id
        try:
            meta = MetaFeedback.create(**args)
            return meta_feedback_schema.dump(meta), 201
        except ValueError as e:
            abort(400, message=str(e))


class CommentResource(Resource):
    method_decorators = [jwt_required]

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("value", type=str, required=True)
        self.parser.add_argument("course_id", type=int, required=True)
        self.parser.add_argument("assignment_id", type=int, required=True)
        self.parser.add_argument("submission_id", type=int)
        self.parser.add_argument("recipient_id", type=int, required=True)

        self.get_parser = reqparse.RequestParser()
        self.get_parser.add_argument("course_id", type=int, required=True)
        self.get_parser.add_argument("assignment_id", type=int, required=True)
        self.get_parser.add_argument("recipient_id", type=int, required=True)

        super(CommentResource, self).__init__()

    def get(self):
        args = self.get_parser.parse_args()
        user = get_current_user()
        owner = user.id == args["recipient_id"]
        ta_or_teacher = user_is_ta_or_teacher(user, args["course_id"])
        grader = Feedback.query.filter(
            Feedback.course_id == args["course_id"],
            Feedback.assignment_id == args["assignment_id"],
            Feedback.receiver_id == args["recipient_id"],
            Feedback.reviewer_id == user.id,
            Feedback.draft.is_(False),
        ).first()
        if not (owner or grader or ta_or_teacher):
            return abort(403)

        comments = (
            Comment.query.filter(
                Comment.course_id == args["course_id"],
                Comment.assignment_id == args["assignment_id"],
                Comment.recipient_id == args["recipient_id"],
            )
            .options(joinedload(Comment.likes).joinedload(CommentLike.user))
            .all()
        )
        return comment_schema.jsonify(comments, many=True)

    def post(self):
        args = self.parser.parse_args()
        user = get_current_user()
        moderator = user_is_ta_or_teacher(user, args["course_id"])
        owner = user.id == args["recipient_id"]
        # get the course and assignment name from a sample task
        feedback = Feedback.query.filter(
            Feedback.receiver_id == args["recipient_id"],
            Feedback.reviewer_id == user.id,
            Feedback.assignment_id == args["assignment_id"],
        ).first()

        if not (owner or moderator or feedback):
            abort(400, message=errors.NOT_PAIRED)

        if not (owner or moderator or not feedback.draft):
            abort(400, message=errors.FEEDBACK_NOT_SUBMITTED)

        if owner or moderator:
            feedback = Feedback.query.filter_by(
                assignment_id=args["assignment_id"]
            ).first()

        if not feedback:
            abort(400, message=errors.COURSE_NOT_SETUP)

        args["commenter_id"] = user.id
        try:
            comment = Comment.create(
                **args,
                course_name=feedback.course_name,
                assignment_name=feedback.assignment_name
            )
        except AssertionError as e:
            abort(400, message=str(e))

        notify_discussion_participants.queue(comment.id)
        if app.config.get("SEND_NOTIFICATION_EMAILS"):
            send_discussion_notification.queue(comment.id)
        return comment_schema.dump(comment), 201


class CommentLikeResource(Resource):
    method_decorators = [jwt_required]

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("comment_id", type=int, required=True)

    def post(self):
        args = self.parser.parse_args()
        user = get_current_user()
        existing = CommentLike.query.filter_by(
            comment_id=args["comment_id"], user_id=user.id
        ).first()
        if existing:
            return "", 409
        comment = Comment.query.get(args["comment_id"])
        if not comment:
            return "", 400

        like = CommentLike.create(user_id=user.id, comment_id=args["comment_id"])
        like.save()
        # Award Medal if possible
        award_super_commentator.queue(args["comment_id"])
        notification = Notification.create(
            item=Notification.LIKE,
            item_id=args["comment_id"],
            course_id=comment.course_id,
            course_name=comment.course_name,
            assignment_id=comment.assignment_id,
            assignment_name=comment.assignment_name,
            user_id=comment.recipient_id,
            recipient_id=comment.commenter_id,
            notifier_id=user.id,
        )
        notification.save()

        return like_schema.dump(like), 201

    def delete(self, like_id):
        user = get_current_user()
        like = CommentLike.query.get(like_id)
        if not like:
            abort(404)
        if like.user_id != user.id:
            abort(401, message="Only owners of likes can delete them")
        like.delete()
        return "", 204


class ExtraFeedbackResource(Resource):
    method_decorators = [jwt_required]

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("course_id", type=int, required=True)
        self.parser.add_argument("assignment_id", type=int, required=True)

    def get(self):
        """Get the active extra feedback request the user has placed"""
        user = get_current_user()
        args = self.parser.parse_args()
        extra = ExtraFeedback.query.filter(
            ExtraFeedback.course_id == args["course_id"],
            ExtraFeedback.assignment_id == args["assignment_id"],
            ExtraFeedback.user_id == user.id,
            ExtraFeedback.active.is_(True),
        ).first()
        return extra_feedback_schema.jsonify(extra)

    def post(self):
        args = self.parser.parse_args()
        user = get_current_user()

        existing = (
            ExtraFeedback.query.filter(ExtraFeedback.course_id == args["course_id"])
            .filter(ExtraFeedback.assignment_id == args["assignment_id"])
            .filter(ExtraFeedback.user_id == user.id)
            .filter(ExtraFeedback.active.is_(True))
            .first()
        )
        if existing:
            return abort(409)

        extra = ExtraFeedback.create(**args, active=True, user_id=user.id)
        extra.save()
        return extra_feedback_schema.dump(extra), 201

    def delete(self, extra_id):
        user = get_current_user()
        e_request = ExtraFeedback.query.get(extra_id)
        if not e_request:
            abort(404)
        if e_request.user_id != user.id:
            abort(401, message="Only owners can delete their request.")
        e_request.delete()
        return "", 204
