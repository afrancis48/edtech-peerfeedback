import math
from collections import defaultdict

from flask import request, jsonify, current_app as app, url_for, redirect
from flask_jwt_extended import get_current_user, get_jwt_identity, jwt_required
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from dateutil.parser import parse as parse_date
from datetime import timedelta

from peerfeedback.api import errors
from peerfeedback.api.jobs.pairing import (
    pair_using_csv,
    pair_automatically,
    allocate_students_to_tas,
)
from peerfeedback.api.jobs.sendmail import send_pairing_email
from peerfeedback.api.schemas import pairing_with_task, real_user_schema, real_pairing
from peerfeedback.api.utils import (
    allowed_roles,
    get_course_teacher,
    get_canvas_client,
    create_pairing,
    required_params,
    validate_csv_input,
)
from peerfeedback.api.views import api_blueprint
from peerfeedback.extensions import db
from peerfeedback.models import User, Pairing, Task

import logging
from rq.job import Job
from peerfeedback.extensions import rq

logger = logging.getLogger("pairing")


@api_blueprint.route("/pairing/manual/", methods=["POST"])
@required_params("course_id", "assignment_id", "grader", "recipient")
@allowed_roles("teacher", "ta")
def manual_pairing():
    """Creates a pairing between the two given users for the specified course
    and assignment. Only one set of grader and recipient values are accepted.
    """
    params = request.get_json()
    course_id = int(params["course_id"])
    assignment_id = int(params["assignment_id"])
    grader_id = params.get("grader")
    recipient_id = params.get("recipient")

    # Grader can't be same as recipient
    if grader_id == recipient_id:
        return (jsonify({"message": errors.GRADER_RECIPIENT_SAME}), 400)

    grader = User.query.filter(User.canvas_id == grader_id).first()
    recipient = User.query.filter(User.canvas_id == recipient_id).first()
    if not grader or not recipient:
        return (jsonify({"message": errors.CANNOT_FIND_STUDENT}), 400)

    teacher = get_course_teacher(course_id)
    if not teacher:
        return jsonify({"message": errors.CANNOT_FIND_TEACHER}), 400

    canvas = get_canvas_client(teacher.canvas_access_token)
    course = canvas.get_course(course_id)
    assignment = course.get_assignment(assignment_id)
    submission = assignment.get_submission(recipient.canvas_id)
    if not submission:
        msg = recipient.name + " has not submitted the assignment."
        return jsonify({"message": msg}), 400

    try:
        creator = get_current_user()
        pair = create_pairing(creator, grader, recipient, course, assignment)
    except errors.PairingExists:
        return jsonify({"message": errors.PAIRING_EXISTS}), 409

    if app.config.get("SEND_NOTIFICATION_EMAILS", False):
        send_pairing_email.queue(pair.id)
    return "", 201


@api_blueprint.route("/pairing/csv/", methods=["POST"])
@required_params("course_id", "assignment_id", "pairs", "allowMissing", "graderType")
@allowed_roles("teacher", "ta")
def csv_pairing():
    params = request.get_json()
    user = get_jwt_identity()
    job = pair_using_csv.queue(
        params["course_id"],
        params["assignment_id"],
        params["pairs"],
        params["allowMissing"],
        params["graderType"],
        user["id"],
        app.config.get("SEND_NOTIFICATION_EMAILS", False),
    )
    return jsonify(dict(id=job.id))


@api_blueprint.route("/pairing/csv/schedule/", methods=["POST"])
@required_params("course_id", "assignment_id", "pairs", "allowMissing", "graderType")
@allowed_roles("teacher", "ta")
def schedule_csv_pairing():
    params = request.get_json()
    if "schedule_time" in params:
        schedule_time = parse_date(params["schedule_time"])
    else:
        error = dict(status="error", message="Missing schedule time")
        return jsonify(error), 400

    validation = validate_csv_input(
        params["course_id"], params["pairs"], params["graderType"]
    )
    if validation["status"] == "error":
        return jsonify(validation), 400

    user = get_jwt_identity()
    job = pair_using_csv.schedule(
        schedule_time,
        params["course_id"],
        params["assignment_id"],
        params["pairs"],
        params["allowMissing"],
        params["graderType"],
        user["id"],
        app.config.get("SEND_NOTIFICATION_EMAILS", False),
        queue="scheduled",
        timeout=60 * 30,
    )
    return jsonify(dict(id=job.id))


@api_blueprint.route("/pairing/automatic/", methods=["POST"])
@required_params(
    "course_id",
    "assignment_id",
    "reviewRounds",
    "excludeDefaulters",
    "excludedStudents",
)
@allowed_roles("teacher", "ta")
def automatic_pairing():
    params = request.get_json()

    teacher = get_course_teacher(params["course_id"])
    if not teacher:
        return jsonify({"message": errors.CANNOT_FIND_TEACHER}), 400

    job_id = f'{params["course_id"]}-{params["assignment_id"]}-{teacher.id}'

    try:
        redis = rq.connection
        prev_job = Job.fetch(job_id, connection=redis)

        job_status = prev_job.get_status()

        # queued, started, deferred, finished, stopped, scheduled, canceled, failed
        if job_status != "finished":
            res = {
                "id": prev_job.id,
                "message": errors.AUTOMATIC_PAIRING_EXISTS,
                "job_status": job_status,
            }
            return jsonify(res), 400
    except Exception as e:
        logger.exception(e)

    job = pair_automatically.queue(
        params["course_id"],
        params["assignment_id"],
        int(params.get("reviewRounds")),
        teacher.id,
        bool(params.get("excludeDefaulters")),
        params.get("excludedStudents"),
        app.config.get("SEND_NOTIFICATION_EMAILS", False),        
        job_id=job_id,
    )
    return jsonify(dict(id=job.id))


@api_blueprint.route("/pairing/automatic/schedule/", methods=["POST"])
@required_params(
    "course_id",
    "assignment_id",
    "reviewRounds",
    "excludeDefaulters",
    "excludedStudents",
)
@allowed_roles("teacher", "ta")
def schedule_automatic_pairing():
    params = request.get_json()
    user = get_current_user()
    custom_time = False
    if "schedule_time" in params:
        schedule_time = parse_date(params["schedule_time"])
        custom_time = True
    else:
        canvas = get_canvas_client(user.canvas_access_token)
        course = canvas.get_course(int(params["course_id"]))
        assignment = course.get_assignment(int(params["assignment_id"]))
        if not assignment.due_at:
            return jsonify(
                {"status": "error", "message": "Due date not set for the assignment"}
            )
        schedule_time = parse_date(assignment.due_at) + timedelta(hours=1)

    job = pair_automatically.schedule(
        schedule_time,
        params["course_id"],
        params["assignment_id"],
        int(params.get("reviewRounds")),
        user.id,
        bool(params.get("excludeDefaulters")),
        params.get("excludedStudents"),
        app.config.get("SEND_NOTIFICATION_EMAILS", False),
        queue="scheduled" if custom_time else "high",
        timeout=60 * 30,
    )
    return jsonify(dict(id=job.id))


@api_blueprint.route("/pairing/ta/", methods=["POST"])
@required_params("course_id", "assignment_id", "allocation")
@allowed_roles("teacher", "ta")
def ta_pairing():
    user = get_current_user()
    params = request.get_json()
    job = allocate_students_to_tas.queue(
        params["course_id"],
        params["assignment_id"],
        user.id,
        params["allocation"],
        app.config.get("SEND_NOTIFICATION_EMAILS", False),
    )
    return jsonify(dict(id=job.id))


@api_blueprint.route(
    "/course/<int:course_id>/assignment/<int:assignment_id>/pairs/mine/"
)
@jwt_required
def get_my_pairings(course_id, assignment_id):
    """Returns a list of pairs for the given course and assignment.
    It returns all the pairs the student is associated with, either as grader
    or recipient.

    :param course_id: Canvas ID of the course
    :param assignment_id: Canvas ID of the assignment
    :return: list of pairs
    """
    user = get_current_user()
    pairs = (
        Pairing.query.filter(
            Pairing.course_id == course_id,
            Pairing.assignment_id == assignment_id,
            (Pairing.grader_id == user.id) | (Pairing.recipient_id == user.id),
            Pairing.archived.is_(False),
        )
        .options(
            joinedload(Pairing.task),
            joinedload(Pairing.recipient),
            joinedload(Pairing.grader),
        )
        .filter(Pairing.task.has(Task.status != "ARCHIVED"))
        .all()
    )
    pair_dicts = pairing_with_task.dump(pairs, many=True)
    if pairs and pairs[0].type == Pairing.IGR:
        for pair in pair_dicts:
            if pair["grader"]["id"] != user.id:
                pair["grader"] = {"id": 0, "name": "Team member"}
    return jsonify(pair_dicts)


@api_blueprint.route("/course/<int:course_id>/assignment/<int:assignment_id>/pairs/")
@allowed_roles("teacher", "ta")
def get_pairings(course_id, assignment_id):
    """Returns a paginated list of pairs for the given course and assignment.
    If the request is made by a Teacher or a TA, the list contains all pairs of
    10 students per page.

    :param course_id: Canvas ID of the course
    :param assignment_id: Canvas ID of the assignment
    :return: list of pairs
    """
    page = request.args.get("page", 1, int)
    per_page = request.args.get("per_page", 10, int)
    start = (page - 1) * per_page
    next_ = None
    pair_query = Pairing.query.filter(
        Pairing.course_id == course_id,
        Pairing.assignment_id == assignment_id,
        Pairing.archived.is_(False),
        or_(Pairing.view_only.is_(False), Pairing.view_only is None)
    ).options(
        joinedload(Pairing.task),
        joinedload(Pairing.grader),
        joinedload(Pairing.recipient),
    )

    pair_graders = (
        db.session.query(Pairing.grader_id)
        .filter(
            Pairing.course_id == course_id,
            Pairing.assignment_id == assignment_id,
            Pairing.archived.is_(False),
            or_(Pairing.view_only.is_(False), Pairing.view_only is None)
        )
        .distinct()
        .all()
    )
    graders = (
        User.query.filter(User.id.in_(pair_graders)).order_by(User.real_name).all()
    )
    # alphabetical ordering of the graders
    grader_ids = list(g.id for g in graders)[start : start + per_page]

    if len(graders) / per_page > page:
        next_ = url_for(
            ".get_pairings",
            course_id=course_id,
            assignment_id=assignment_id,
            page=page + 1,
        )

    pairs = pair_query.filter(Pairing.grader_id.in_(grader_ids)).all()
    pairs = format_pairs(grader_ids, graders, pairs)
    data = {
        "page": page,
        "per_page": per_page,
        "pairs": pairs,
        "page_count": math.ceil(len(graders) / per_page),
    }
    if next_:
        data["next"] = next_
    return jsonify(data)


def format_pairs(grader_ids, graders, pairs):
    """Converts the pair objects from sql models to dict for sending as JSON

    :param grader_ids: list of grader ids
    :param graders: list of graders objects
    :param pairs: result of Pairing.query
    :return: list of dict(grader, list(recipients))
    """
    grader_map = dict((g.id, g) for g in graders if g.id in grader_ids)
    pair_table = defaultdict(list)
    for p in pairs:
        pair_table[p.grader.id].append(p)
    pairs = [
        dict(
            grader=real_user_schema.dump(grader_map[g]),
            pairing=real_pairing.dump(pair_table[g], many=True),
        )
        for g in grader_ids
        if pair_table[g]
    ]
    return pairs


@api_blueprint.route(
    "/course/<int:course_id>/assignment/<int:assignment_id>/pairs/search"
)
@allowed_roles("teacher", "ta")
def search_pairs(course_id, assignment_id):
    """Search function for pairings in the database.

    :param course_id: canvas id of the course
    :param assignment_id: canvas id of the assignment
    """
    grader = request.args.get("grader", False, type=str)
    recipient = request.args.get("recipient", False, type=str)
    if not (grader or recipient):
        return redirect(
            url_for(".get_pairings", course_id=course_id, assignment_id=assignment_id)
        )

    q = Pairing.query.filter(
        Pairing.course_id == course_id,
        Pairing.assignment_id == assignment_id,
        Pairing.archived.is_(False),
    ).options(
        joinedload(Pairing.task),
        joinedload(Pairing.grader),
        joinedload(Pairing.recipient),
    )
    grader_ids = None
    graders = None
    if grader:
        graders = (
            User.query.filter(User.name.ilike(f"%{grader}%")).order_by(User.name).all()
        )
        grader_ids = [g.id for g in graders]
        q = q.filter(Pairing.grader_id.in_([g.id for g in graders]))
    if recipient:
        recipient = request.args.get("recipient", type=str)
        recipients = User.query.filter(User.name.ilike(f"%{recipient}%")).all()
        q = q.filter(Pairing.recipient_id.in_([r.id for r in recipients]))

    pairs = q.all()
    if recipient:
        grader_ids = list(set(p.grader_id for p in pairs))
        graders = User.query.filter(User.id.in_(grader_ids)).order_by(User.name).all()
    pairs = format_pairs(grader_ids, graders, pairs)
    return jsonify(pairs)
