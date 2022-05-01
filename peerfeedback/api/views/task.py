from flask import jsonify, abort, current_app as app
from flask_jwt_extended import jwt_required, get_current_user
from sqlalchemy.orm import joinedload
from werkzeug.exceptions import abort

from peerfeedback.api import errors
from peerfeedback.api.jobs.pairing import replace_task_and_generate_new_pairing
from peerfeedback.api.schemas import task_with_pairing
from peerfeedback.api.views import api_blueprint
from peerfeedback.models import Pairing, Task


@api_blueprint.route(
    "/course/<int:course_id>/assignment/<int:assignment_id>/user/<int:user_id>/task/"
)
@jwt_required
def get_task_for_submission(course_id, assignment_id, user_id):
    """Get the task of the requesting user associated with a particular submission

    :param course_id: canvas id of the course
    :param assignment_id: canvas id of the assignment
    :param user_id: id of submitter
    :return: task as JSON
    """
    current_user = get_current_user()
    pair = Pairing.query.filter(
        Pairing.course_id == course_id,
        Pairing.assignment_id == assignment_id,
        Pairing.recipient_id == user_id,
        Pairing.grader_id == current_user.id,
        Pairing.archived.is_(False),
    ).first()
    if not pair:
        return abort(404)
    task = (
        Task.query.filter(Task.pairing_id == pair.id)
        .options(joinedload(Task.pairing))
        .first()
    )
    return task_with_pairing.jsonify(task)


@api_blueprint.route("/task/<int:task_id>/replace/", methods=["POST"])
@jwt_required
def replace_task(task_id):
    """Archives the given task and creates a new pairing and task for the user.
    This is usually when the task assigned to the user becomes invalid due to
    the submission going missing after the pairing is complete.

    :param task_id: id of the task to be replaced
    :return: task object
    """
    task = Task.query.get(task_id)
    if not task:
        return jsonify({"message": errors.TASK_NOT_FOUND}), 404

    user = get_current_user()
    if task.user_id != user.id:
        return abort(403)

    job = replace_task_and_generate_new_pairing.queue(
        task_id, app.config.get("SEND_NOTIFICATION_EMAILS", False)
    )
    return jsonify(dict(id=job.id))
