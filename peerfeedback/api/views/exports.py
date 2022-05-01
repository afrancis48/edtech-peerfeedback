from flask import jsonify, request
from flask_jwt_extended import get_current_user, jwt_required

from peerfeedback.api import errors
from peerfeedback.api.jobs.exports import (
    export_assignment_data,
    export_course_data,
    export_student_scores,
    export_igr_data,
)
from peerfeedback.api.utils import allowed_roles, user_is_ta_or_teacher
from peerfeedback.api.views import api_blueprint
from peerfeedback.models import AssignmentSettings


@api_blueprint.route("/course/<int:course_id>/assignment/<int:assignment_id>/data/")
@allowed_roles("teacher", "ta")
def get_assignment_data(course_id, assignment_id):
    user = get_current_user()
    assign_settings = AssignmentSettings.query.filter_by(
        assignment_id=assignment_id
    ).first()
    if assign_settings.intra_group_review:
        job = export_igr_data.queue(course_id, assignment_id, user.id)
    else:
        job = export_assignment_data.queue(course_id, assignment_id, user.id)
    return jsonify(dict(id=job.id))


@api_blueprint.route("/course/<int:course_id>/data/", methods=["POST"])
@allowed_roles("teacher", "ta")
def get_course_data(course_id):
    user = get_current_user()
    data = request.get_json()
    include_drafts = False
    if "include_drafts" in data:
        include_drafts = data["include_drafts"]
    ai_feedback = False
    if "ai_feedback" in data:
        ai_feedback = data["ai_feedback"]
    job = export_course_data.queue(course_id, user.id, include_drafts, ai_feedback)
    return jsonify(dict(id=job.id))


@api_blueprint.route(
    "/course/<int:course_id>/assignment/<int:assignment_id>/detailed-data/",
    methods=["POST"],
)
@allowed_roles("teacher", "ta")
def get_detailed_assignment_data(course_id, assignment_id):
    user = get_current_user()
    include_drafts = True
    ai_feedback = True
    job = export_course_data.queue(
        course_id, user.id, include_drafts, ai_feedback, assignment_id
    )
    return jsonify({"id": job.id})


@api_blueprint.route("/course/<int:course_id>/assignment/<int:assignment_id>/scores/")
@jwt_required
def export_assignment_scores(course_id, assignment_id):
    user = get_current_user()
    if not user_is_ta_or_teacher(user, course_id):
        return jsonify({"status": "error", "message": errors.ONLY_TEACHERS}), 400
    assignment = AssignmentSettings.query.filter_by(assignment_id=assignment_id).first()
    if not assignment.rubric_id:
        return jsonify({"status": "error", "message": errors.NO_RUBRIC_SCORES}), 400
    job = export_student_scores.queue(course_id, assignment_id, user.id)
    return jsonify(dict(id=job.id))
