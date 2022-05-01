from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_current_user
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from peerfeedback.api import errors
from peerfeedback.api.schemas import rubric_schema, full_rubric
from peerfeedback.api.views import api_blueprint
from peerfeedback.extensions import db
from peerfeedback.models import (
    Rubric,
    AssignmentSettings,
    CourseUserMap,
    RubricCriteria,
)


@api_blueprint.route("/rubrics/")
@jwt_required
def get_rubrics():
    """Fetch all the public rubrics and the rubrics of the user

    :return: list of rubrics as JSON
    """
    user = get_current_user()
    rubrics = Rubric.query.filter(
        (Rubric.owner_id == user.id) | (Rubric.public.is_(True)),
        Rubric.active.is_(True),
    ).all()

    return rubric_schema.jsonify(rubrics, many=True)


@api_blueprint.route("/rubrics/mine/")
@jwt_required
def get_my_rubrics():
    """Fetch all the rubric created by the user

    :return: list of rubrics as JSON
    """
    user = get_current_user()
    rubrics = Rubric.query.filter(Rubric.owner_id == user.id).all()
    rubrics_used = (
        db.session.query(
            AssignmentSettings.rubric_id, func.count(AssignmentSettings.id)
        )
        .group_by(AssignmentSettings.rubric_id)
        .all()
    )
    rubric_assignment_map = {r[0]: r[1] for r in rubrics_used}

    rubrics = rubric_schema.dump(rubrics, many=True)
    for rubric in rubrics:
        rubric["in_use"] = bool(rubric_assignment_map.get(rubric["id"], 0))

    return jsonify(rubrics)


@api_blueprint.route("/rubric/", methods=["POST"])
@jwt_required
def create_rubric():
    """Saves the rubric and the rubric criteria in the database. The user
    creating the rubric should be a teacher or a TA in at least one of the
    courses.

    :return: HTTP 201 if successful
    """
    user = get_current_user()
    mapping = CourseUserMap.query.filter(
        CourseUserMap.user_id == user.id,
        (CourseUserMap.role == CourseUserMap.TA)
        | (CourseUserMap.role == CourseUserMap.TEACHER),
    ).first()
    if not mapping:
        return jsonify({"message": errors.ONLY_TEACHERS}), 403

    rubric = request.get_json()

    if not rubric["name"]:
        return jsonify({"message": errors.INVALID_RUBRIC_NAME}), 400

    rubric_obj = Rubric.create(
        name=rubric["name"],
        description=rubric.get("description", ""),
        public=rubric.get("public", True),
        owner_id=user.id,
    )
    rubric_obj.save()

    try:
        for criteria in rubric["criterions"]:
            RubricCriteria.create(
                name=criteria["name"],
                description=criteria.get("description", ""),
                levels=criteria["levels"],
                rubric_id=rubric_obj.id,
            )
    except AssertionError as e:
        return jsonify({"message": str(e)}), 400

    return "", 201


@api_blueprint.route("/rubric/<int:rubric_id>/", methods=["GET", "PUT"])
@jwt_required
def get_rubric(rubric_id):
    """Get the full rubric with the specified id. Includes all the criterions.

    :param rubric_id: id of the rubric
    :return: rubric with all the criterions
    """
    rubric = Rubric.query.get(rubric_id)

    if not rubric:
        return "", 404

    if request.method == "PUT":
        args = request.get_json()
        if "public" in args and isinstance(args["public"], bool):
            rubric.public = args["public"]
        if "active" in args and isinstance(args["active"], bool):
            rubric.active = args["active"]
        rubric.save()

    criterions = (
        RubricCriteria.query.filter_by(rubric_id=rubric_id)
        .order_by(RubricCriteria.id)
        .all()
    )
    rubric.criterions = criterions

    return full_rubric.jsonify(rubric)
