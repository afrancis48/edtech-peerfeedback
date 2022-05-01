import requests

from flask import request, jsonify, Response, current_app as app
from flask_jwt_extended import jwt_required

from peerfeedback.api.views import api_blueprint
from peerfeedback.api import errors


@api_blueprint.route("/grade-feedback/", methods=["POST"])
@jwt_required
def grade_feedback():
    """Generates a ML grading of the feedback text and returns the grade
    and the confidence value

    :returns: the ML grade of the feedback and the confidence levels
    """
    data = request.get_json()
    if not isinstance(data, dict) or "value" not in data:
        return jsonify({"status": "error", "message": errors.MISSING_PARAMS}), 400

    url = app.config.get("MLAPP_URL") + "/grade-feedback/"
    res = requests.post(url, json=data)

    return Response(
        res.content, mimetype=res.headers["Content-Type"], status=res.status_code
    )
