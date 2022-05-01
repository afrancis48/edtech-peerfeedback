# -*- coding: utf-8 -*-
"""The blueprint serving the API"""
import itertools

from datetime import datetime
from collections import defaultdict
from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_current_user

from peerfeedback.api.views import api_blueprint
from peerfeedback.utils import get_pseudo_names
from peerfeedback.models import (
    User,
    Pairing,
    Feedback,
    Notification,
    ExtraFeedback,
    Medal,
    Study,
)
from peerfeedback.extensions import db, cache
from peerfeedback.api.utils import get_canvas_client, get_course_teacher, allowed_roles
from peerfeedback.api import errors
from peerfeedback.api.schemas import medal_schema, user_schema


@cache.memoize(timeout=60 * 60 * 8)
def get_submissions_users(course_id, assignment_id):
    teacher = get_course_teacher(course_id)

    if not teacher:
        raise errors.TeacherNotFoundException("Course teacher not found")

    canvas = get_canvas_client(teacher.canvas_access_token)
    course = canvas.get_course(course_id)
    assignment = course.get_assignment(assignment_id)
    submissions = assignment.get_submissions()
    ids = [
        s.user_id
        for s in submissions
        if s.workflow_state == "submitted"
        or (s.workflow_state == "graded" and s.score != None and int(s.score) != 0)
        and not s.missing
    ]
    users = User.query.filter(User.canvas_id.in_(ids)).all()

    return users


@api_blueprint.route("/course/<int:course_id>/assignment/<int:assignment_id>/peers/")
@allowed_roles("student")
def get_peers(course_id, assignment_id):
    """Get a list of students enrolled in the same course as the requesting
    student, along with the information of how many feedback they have recieved
    and if they have requested extra feedback for their submission.

    :param course_id: canvas id of the course
    :param assignment_id: canvas id of the assignment
    :return: list of students with their feedback count and extra requests
    """
    try:
        users = get_submissions_users(course_id, assignment_id)
    except errors.TeacherNotFoundException:
        return jsonify({"message": errors.CANNOT_FIND_TEACHER}), 400

    current_user = get_current_user()

    # Skip the users who have been paired with the current user
    pairs = Pairing.query.filter(
        Pairing.course_id == course_id,
        Pairing.assignment_id == assignment_id,
        Pairing.grader_id == current_user.id,
    ).all()
    already_paired = [p.recipient_id for p in pairs]
    already_paired.append(current_user.id)  # skip self
    users = [user for user in users if user.id not in already_paired]
    user_ids = [user.id for user in users]

    # filter students who have requested extra feedback
    extra_requests = (
        ExtraFeedback.query.filter(ExtraFeedback.course_id == course_id)
        .filter(ExtraFeedback.assignment_id == assignment_id)
        .filter(ExtraFeedback.user_id.in_(user_ids))
        .filter(ExtraFeedback.active.is_(True))
        .all()
    )
    users_with_requests = [e.user_id for e in extra_requests]

    # existing feedback
    feedbacks = (
        Feedback.query.filter(Feedback.course_id == course_id)
        .filter(Feedback.assignment_id == assignment_id)
        .filter(Feedback.receiver_id.in_(user_ids))
        .all()
    )

    feedback_map = defaultdict(int)
    for feed in feedbacks:
        feedback_map[feed.receiver_id] += 1

    # Add a Pseudo name for the study
    studies = Study.query.filter(
        Study.start_date < datetime.now(), Study.end_date > datetime.now()
    ).all()
    active_study = None
    for study in studies:
        if not study.assignments:
            continue
        assignments = study.assignments.split(",")
        if str(assignment_id) in assignments:
            active_study = study

    participants = []
    pseudo_names = []
    if active_study:
        participants = [p.id for p in active_study.participants]
        pseudo_names = itertools.cycle(get_pseudo_names())

    peers = []
    for user in users:
        peer = user_schema.dump(user)
        if current_user.id in participants and user.id in participants:
            peer["name"] = next(pseudo_names)
            peer["avatar_url"] = ""
        peer["feedbacks"] = feedback_map.get(user.id, 0)
        peer["extra_requested"] = user.id in users_with_requests
        peers.append(peer)

    return jsonify(peers)


@api_blueprint.route("/medals/")
@jwt_required
def get_medals():
    if request.args.get("user", None):
        user_id = int(request.args.get("user"))
        medals = Medal.query.filter_by(user_id=user_id).all()
    else:
        medals = get_current_user().medals
    return medal_schema.jsonify(medals, many=True)


@api_blueprint.route(
    "/course/<int:course_id>/assignment/<int:assignment_id>/extras_given/"
)
@jwt_required
def get_count_of_extra_feedback_given(course_id, assignment_id):
    user = get_current_user()
    pairs = Pairing.query.filter(
        Pairing.course_id == course_id,
        Pairing.assignment_id == assignment_id,
        Pairing.grader_id == user.id,
        Pairing.creator_id == user.id,
        Pairing.type == Pairing.STUDENT,
    ).all()
    return str(len(pairs))


@api_blueprint.route("/notifications/clear/", methods=["POST"])
@jwt_required
def clear_notifications():
    """Mark all the notifications of the user a read"""
    user = get_current_user()
    db.session.query(Notification).filter(Notification.recipient_id == user.id).update(
        dict(read=True)
    )
    db.session.commit()
    return "OK"
