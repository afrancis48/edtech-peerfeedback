import re

from canvasapi.exceptions import ResourceDoesNotExist
from flask import current_app as app, abort, jsonify, request
from flask_jwt_extended import jwt_required, get_current_user
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from peerfeedback.api import errors
from peerfeedback.api.schemas import (
    feedback_with_rating,
    full_feedback,
    feedback_schema,
)
from peerfeedback.api.utils import (
    get_canvas_client,
    get_course_teacher,
    user_is_ta_or_teacher,
)
from peerfeedback.api.views import api_blueprint
from peerfeedback.extensions import db
from peerfeedback.models import Feedback, Pairing, AssignmentSettings, Task, User


@api_blueprint.route(
    "/course/<int:course_id>/assignment/<int:assignment_id>/user/<int:user_id>/feedbacks/"
)
@jwt_required
def submission_feedbacks(course_id, assignment_id, user_id):
    """Get the feedback submitted for a particular user's submission

    :param course_id: canvas id of the course
    :param assignment_id: canvas id of the assignment
    :param user_id: id of the user who is the recipient of the feedback
    :return: list of feedback as JSON
    """
    query = (
        Feedback.query.filter(
            Feedback.course_id == course_id,
            Feedback.assignment_id == assignment_id,
            Feedback.receiver_id == user_id,
            Feedback.draft.is_(False),
            Feedback.pairing.has(Pairing.archived.is_(False)),
        )
        .options(joinedload(Feedback.reviewer))
        .options(joinedload(Feedback.receiver))
        .options(joinedload(Feedback.rating))
    )
    user = get_current_user()

    # 1. a teacher/ta - should get all feedbacks with ratings
    if user_is_ta_or_teacher(user, course_id):
        return feedback_with_rating.jsonify(query.all(), many=True)

    # 2. a grader - should get all the student feedback if he has submitted his own
    fbs = query.filter(Feedback.type.in_([Feedback.STUDENT, Feedback.IGR])).all()
    grader_fb = next((fb for fb in fbs if fb.reviewer_id == user.id), None)
    if grader_fb:
        # Send the feedbacks with their read and write time information for
        # testing purposes
        if grader_fb.type == Feedback.IGR:
            fbs = [grader_fb]

        if re.match("^dev.*", app.config["ENV"], re.IGNORECASE):
            fb_dicts = full_feedback.dump(fbs, many=True)
        else:
            fb_dicts = feedback_with_rating.dump(fbs, many=True)

        return jsonify(fb_dicts)

    # 3. the assignment submitter - should get all the feedbacks with ratings
    receiver = User.query.get(user_id)
    teacher = get_course_teacher(course_id)
    canvas = get_canvas_client(teacher.canvas_access_token)
    course = canvas.get_course(course_id)
    assignment = course.get_assignment(assignment_id)
    try:
        submission = assignment.get_submission(receiver.canvas_id)
    except ResourceDoesNotExist:
        submission = None

    if submission and submission.user_id == user.canvas_id:
        fb_dicts = feedback_with_rating.dump(query.all(), many=True)
        if fb_dicts[0]["type"] == Feedback.IGR:
            for fb in fb_dicts:
                fb["reviewer"] = {"name": "Team Member"}
        return jsonify(fb_dicts)

    # 4. a random guy with an access token to the API
    return abort(403)


@api_blueprint.route(
    "/course/<int:course_id>/assignment/<int:assignment_id>/user/<int:user_id>/feedback/mine/"
)
@jwt_required
def get_my_feedback(course_id, assignment_id, user_id):
    """Returns the requesting user's feedback on a submission. 404 if not found"""
    current_user = get_current_user()
    feedback = Feedback.query.filter(
        Feedback.course_id == course_id,
        Feedback.assignment_id == assignment_id,
        Feedback.receiver_id == user_id,
        Feedback.reviewer_id == current_user.id,
        Feedback.pairing.has(Pairing.archived.is_(False)),
    ).first()
    if not feedback:
        # Check if the user is paired on not
        pair = (
            Pairing.query.filter(
                Pairing.course_id == course_id,
                Pairing.assignment_id == assignment_id,
                Pairing.recipient_id == user_id,
                Pairing.grader_id == current_user.id,
                Pairing.archived.is_(False),
            )
            .options(joinedload(Pairing.task))
            .first()
        )

        if not pair:
            return abort(404)

        # If the pairing exists but not the feedback, then it was probably a
        # pairing done before the feedback POST endpoint was removed. In that
        # case create a new feedback object and return it to the user.
        settings = AssignmentSettings.query.filter_by(
            assignment_id=assignment_id
        ).first()
        pair.task.status = Task.IN_PROGRESS
        pair.task.save()

        feedback = Feedback.create(
            type=pair.type,
            draft=True,
            assignment_name=pair.task.assignment_name,
            assignment_id=assignment_id,
            course_name=pair.task.course_name,
            course_id=course_id,
            read_time=0,
            write_time=0,
            grades=[],
            receiver_id=user_id,
            reviewer_id=current_user.id,
            pairing_id=pair.id,
            rubric_id=settings.rubric_id,
        )
        feedback.save()

    return full_feedback.jsonify(feedback)


@api_blueprint.route("/assignment/settings/<int:settings_id>/rubric/affected/")
@jwt_required
def feedback_affected_by_current_rubric(settings_id):
    """Returns the number of feedback that have been submitted in a given assignment
    using the existing rubric.

    This is a utility for checking if changing the rubric for an assignment will
    affect the users who have already submitted an evaluation using the existing
    rubric.

    :param settings_id: id of the AssignmentSettings object
    :return: dict of rubric_id and affected feedback count
    """
    settings = AssignmentSettings.query.get(settings_id)
    if not settings:
        return jsonify({"message": errors.ASSIGNMENT_NOT_SETUP}), 404

    q = db.session.query(func.count(Feedback.id)).filter(
        Feedback.assignment_id == settings.assignment_id, Feedback.draft.is_(False)
    )
    if settings.rubric_id:
        q = q.filter(Feedback.rubric_id == settings.rubric_id)
    count = q.scalar()
    return jsonify({"feedback_count": count, "rubric_id": settings.rubric_id})


@api_blueprint.route("/feedback/all/")
@jwt_required
def all_user_feedback():
    """Get all the feedback ever given by a user

    :return:  paginated list of all the feedback from the user
    """
    user = get_current_user()
    page = request.args.get("page", 1, int)
    course = request.args.get("course", 0, int)
    sort_by = request.args.get("sort_by", "newest", str)
    query = Feedback.query.filter(
        Feedback.reviewer_id == user.id, Feedback.draft.is_(False)
    )
    if sort_by == "newest":
        query = query.order_by(Feedback.end_date.desc())
    elif sort_by == "oldest":
        query = query.order_by(Feedback.end_date)

    if course:
        query = query.filter(Feedback.course_id == course)
    feedback_page = query.paginate(page, 10, False)
    data = {
        "feedback": feedback_schema.dump(feedback_page.items, many=True),
        "has_next": feedback_page.has_next,
        "page": page,
        "next": feedback_page.next_num,
        "pages": feedback_page.pages,
        "total": feedback_page.total,
    }

    return jsonify(data)


@api_blueprint.route(
    "/course/<int:course_id>/assignment/<int:assignment_id>/feedbacks/"
)
@jwt_required
def all_submission_feedbacks(course_id, assignment_id):
    """Get the feedback submitted for a particular user's submission

    :param course_id: canvas id of the course
    :param assignment_id: canvas id of the assignment
    :return: list of feedback as JSON
    """
    query = Feedback.query.filter(
            Feedback.course_id == course_id,
            Feedback.assignment_id == assignment_id,
            Feedback.draft.is_(False),
            Feedback.pairing.has(Pairing.archived.is_(False)),
        )
    user = get_current_user()

    # 1. a teacher/ta - should get all feedbacks with ratings
    if user_is_ta_or_teacher(user, course_id):
        return feedback_with_rating.jsonify(query.all(), many=True)

    # 2. a random guy with an access token to the API
    return abort(403)
