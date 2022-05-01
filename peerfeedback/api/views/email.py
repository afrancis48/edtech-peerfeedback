import base64
import re

from bs4 import BeautifulSoup
from email_reply_parser import EmailReplyParser
from flask import request, abort, jsonify, current_app as app
from flask_jwt_extended import jwt_required, get_current_user
from sentry_sdk import capture_exception

from peerfeedback.api.jobs.sendmail import (
    send_support_email,
    send_pending_review_reminder,
)
from peerfeedback.api.utils import (
    post_comment_to_feedback,
    post_reply_to_comment,
    user_is_ta_or_teacher,
)
from peerfeedback.api.views import api_blueprint
from peerfeedback.api import errors


@api_blueprint.route("/inbound/", methods=["POST"])
def inbound_email():
    """Webhook that parses the incoming emails and automatically posts comments"""
    to_regex = re.compile("reply\+(?P<identifier>[a-zA-Z0-9=]+)@", re.IGNORECASE)
    to = request.form.get("to")
    try:
        # Validate the reply_to address used
        assert to_regex.search(to)
    except AssertionError:
        # invalid reply_to address used
        capture_exception()
        return "OK"

    identifier = to_regex.search(to).group("identifier")
    identifier = base64.urlsafe_b64decode(identifier).decode()

    try:
        assert len(identifier.split("_")) > 1
        assert int(identifier.split("_")[1]) > 0
    except (AssertionError, ValueError):
        # invalid identifier
        capture_exception()
        return "OK"

    item_id = int(identifier.split("_")[1])
    user_email = request.form.get("from")
    person_regex = re.compile(r"<(?P<email>.*)>$")
    if person_regex.search(user_email):
        user_email = person_regex.search(user_email).group("email")
    # create a new comment
    if "html" in request.form and request.form.get("html"):
        soup = BeautifulSoup(request.form.get("html"))
        content = EmailReplyParser.parse_reply(soup.text)
    else:
        content = EmailReplyParser.parse_reply(request.form.get("text"))
    if not content:
        return "OK"

    if "feedback" in identifier:
        post_comment_to_feedback(item_id, user_email, content)
    elif "comment" in identifier:
        post_reply_to_comment(item_id, user_email, content)

    return "OK", 200


@api_blueprint.route("/support/email/", methods=["POST"])
@jwt_required
def support_email():
    """Triggers the job to send the support email to the admin

    :return: Success Code
    """
    user = get_current_user()
    email = request.get_json()
    subject = email.get("subject", None)
    message = email.get("message", None)

    if not subject or not message:
        return abort(400)

    if app.config.get("SEND_SUPPORT_EMAILS", False):
        send_support_email.queue(user.id, subject, message)

    return "OK", 200


@api_blueprint.route(
    "/course/<int:course_id>/assignment/<int:assignment_id>/notify/all/",
    methods=["POST"],
)
@api_blueprint.route(
    "/course/<int:course_id>/assignment/<int:assignment_id>/user/<int:grader_id>/notify/",
    methods=["POST"],
)
@jwt_required
def send_pending_review_reminder_emails(course_id, assignment_id, grader_id=None):
    user = get_current_user()
    if not user_is_ta_or_teacher(user, course_id):
        return jsonify({"status": "error", "message": errors.NOT_AUTHORISED}), 403

    if app.config.get("SEND_NOTIFICATION_EMAILS", False):
        send_pending_review_reminder.queue(course_id, assignment_id, grader_id)

    return "OK", 200
