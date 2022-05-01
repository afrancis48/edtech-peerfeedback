import base64
import os
from pathlib import Path

import jinja2
import sendgrid
from peerfeedback.api.utils import (fetch_emailable_users, get_canvas_client,
                                    get_course_teacher, proper_email)
from peerfeedback.extensions import db, rq
from peerfeedback.models import (Comment, CourseUserMap, Feedback, Pairing,
                                 Task, User, UserSettings)
from sendgrid import Email
from sendgrid.helpers.mail import Content, Mail, Personalization
from sentry_sdk import capture_exception, capture_message, push_scope
from sqlalchemy.orm import joinedload

sg = sendgrid.SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
HOSTNAME = "peerfeedback.gatech.edu"
SENDER_HOSTNAME = "peerfeedback.io"


def get_email_template(name):
    return os.path.join(Path(__file__).parents[2], "templates", "email", name)


@rq.job("default")
def send_feedback_notification(feedback_id):
    """Sends a notification email to the recipient of a feedback

    :param feedback_id: ID of the feedback item for which the notification email
        needs to be sent
    """
    feedback = Feedback.query.options(
        joinedload(Feedback.receiver).joinedload(User.settings)
    ).get(feedback_id)

    if feedback.receiver.settings and not feedback.receiver.settings.feedback_emails:
        return

    feedback_url = (
        "https://{0}/app/feedback/course/{1}/assignment/{2}/user/{3}/".format(
            HOSTNAME, feedback.course_id, feedback.assignment_id, feedback.receiver_id
        )
    )
    meta_url = feedback_url + "#feedback{0}".format(feedback_id)

    mail = Mail()
    personalization = Personalization()
    personalization.add_to(
        Email(proper_email(feedback.receiver), feedback.receiver.name)
    )
    mail.add_personalization(personalization)
    mail.from_email = Email("notification@" + SENDER_HOSTNAME, "Peer Feedback")
    identifier = "feedback_{0}".format(feedback.id)
    identifier = base64.urlsafe_b64encode(identifier.encode()).decode()
    mail.reply_to = Email(
        "reply+{0}@parse.{1}".format(identifier, SENDER_HOSTNAME), "Peer Feedback"
    )
    mail.subject = "Feedback from {0} on your assignment {1} in {2}".format(
        feedback.reviewer.name, feedback.assignment_name, feedback.course_name
    )
    if feedback.type == Feedback.IGR:
        mail.subject = (
            "Feedback from a team member for the assignment {0} in {1}".format(
                feedback.assignment_name, feedback.course_name
            )
        )
        mail.reply_to = Email("noreply@" + SENDER_HOSTNAME, "Peer Feedback - No Reply")

    if feedback.type == Feedback.TA:
        mail.subject = "TA {0} gave feedback for your assignment {1} in {2}".format(
            feedback.reviewer.name, feedback.assignment_name, feedback.course_name
        )

    template = get_email_template("new_feedback.html")
    with open(template) as f:
        template = jinja2.Template(f.read())
        content = Content(
            "text/html",
            template.render(
                heading=mail.subject,
                comment=feedback.value,
                feedback_url=feedback_url,
                meta_url=meta_url,
                hostname=HOSTNAME,
            ),
        )
        mail.add_content(content)

    try:
        response = sg.send(mail)
    except Exception as e:
        capture_exception(e)
        return

    if response.status_code >= 400:
        with push_scope() as scope:
            scope.set_extra("response", response)
            capture_message("Email sending failed.")


@rq.job("default")
def send_discussion_notification(comment_id):
    """Sends an email to everyone participating in the discussion with the full
    text of the comment.

    :param comment_id: ID of the comment for which the notification needs to be
        sent
    """
    # shortlist the users to send the emails
    comment = Comment.query.get(comment_id)
    commenter_ids = (
        db.session.query(Comment.commenter_id)
        .filter_by(
            course_id=comment.course_id,
            assignment_id=comment.assignment_id,
            submission_id=comment.submission_id,
            recipient_id=comment.recipient_id,
        )
        .distinct()
    )
    grader_ids = (
        db.session.query(Feedback.reviewer_id)
        .filter_by(
            course_id=comment.course_id,
            assignment_id=comment.assignment_id,
            submission_id=comment.submission_id,
            receiver_id=comment.recipient_id,
        )
        .distinct()
    )
    participant_ids = [cid for (cid,) in commenter_ids] + [gid for (gid,) in grader_ids]
    participant_ids = list(set(participant_ids))

    # Don't send the comment to the commenter
    participant_ids.remove(comment.commenter_id)
    to_users = fetch_emailable_users(participant_ids, "discussion")

    mail = Mail()
    personalization = Personalization()
    for user in to_users:
        personalization.add_to(Email(proper_email(user), user.name))
    mail.add_personalization(personalization)
    mail.from_email = Email("notification@" + SENDER_HOSTNAME, comment.commenter.name)

    identifier = "comment_{0}".format(comment.id)
    identifier = base64.urlsafe_b64encode(identifier.encode()).decode()
    mail.reply_to = Email(
        "reply+{0}@parse.{1}".format(identifier, SENDER_HOSTNAME),
        "Peer Feedback Discussion",
    )

    feedback = Feedback.query.filter_by(
        course_id=comment.course_id, assignment_id=comment.assignment_id
    ).first()
    mail.subject = (
        "New comment on {recipient}'s assignment {assignment} in {course}".format(
            recipient=comment.recipient.name,
            assignment=feedback.assignment_name,
            course=feedback.course_name,
        )
    )

    discussion_url = (
        "https://{0}/app/feedback/course/{1}/assignment/{2}/user/{3}/".format(
            HOSTNAME, comment.course_id, comment.assignment_id, comment.recipient_id
        )
    )
    comment_url = discussion_url + "#comment_{0}".format(comment_id)
    template = get_email_template("new_comment.html")
    with open(template) as f:
        heading = comment.commenter.name + " commented:"
        template = jinja2.Template(f.read())
        content = Content(
            "text/html",
            template.render(
                heading=heading,
                comment=comment.value,
                comment_url=comment_url,
                discussion_url=discussion_url,
                hostname=HOSTNAME,
            ),
        )
        mail.add_content(content)

    if len(to_users):
        response = sg.send(mail)

        if response.status_code >= 400:
            capture_message(
                "Email sending failed. Response code: {0}, Body:"
                " {1}, Headers: {2}".format(
                    response.status_code, response.body, response.headers
                )
            )

    # Notify the user whose assignment is being commented upon
    if comment.recipient.settings.comment_emails:
        send_comment_notification(
            comment, feedback.assignment_name, feedback.course_name, mail.reply_to
        )


def send_comment_notification(comment, assignment, course, reply_to):
    mail = Mail()
    personalization = Personalization()
    discussion_url = (
        "https://{0}/app/feedback/course/{1}/assignment/{2}/user/{3}/".format(
            HOSTNAME, comment.course_id, comment.assignment_id, comment.recipient_id
        )
    )

    mail.from_email = Email("notification@" + SENDER_HOSTNAME, comment.commenter.name)
    personalization.add_to(
        Email(proper_email(comment.recipient), comment.recipient.name)
    )
    mail.add_personalization(personalization)
    mail.reply_to = reply_to
    mail.subject = "New comment on your assignment {assignment} in {course}".format(
        assignment=assignment, course=course
    )

    template = get_email_template("new_comment.html")

    with open(template) as f:
        template = jinja2.Template(f.read())
        heading = comment.commenter.name + " says:"
        comment_url = discussion_url + "#comment_{0}".format(comment.id)
        content = Content(
            "text/html",
            template.render(
                heading=heading,
                comment=comment.value,
                discussion_url=discussion_url,
                comment_url=comment_url,
                hostname=HOSTNAME,
            ),
        )
        mail.add_content(content)

    try:
        response = sg.send(mail)
    except Exception:
        capture_exception()
        return

    if response.status_code >= 400:
        with push_scope() as scope:
            scope.set_extra("response", response)
            capture_message("Email sending failed.", response=response)


@rq.job("default")
def send_pairing_email(pairing_id):
    """Sends an email to the grader of the pairing, intimating them that an
    submission has been assigned to them for evaluation and review.

    :param pairing_id: the pairing whose grader the email is being sent
    """
    pairing = Pairing.query.options(
        joinedload(Pairing.recipient),
        joinedload(Pairing.grader),
        joinedload(Pairing.task),
    ).get(pairing_id)
    if not pairing:
        return False

    mail = Mail()
    personalization = Personalization()
    discussion_url = (
        "https://{0}/app/feedback/course/{1}/assignment/{2}/user/{3}/".format(
            HOSTNAME, pairing.course_id, pairing.assignment_id, pairing.recipient_id
        )
    )
    mail.from_email = Email("notification@" + SENDER_HOSTNAME, "Peer Feedback")
    mail.reply_to = Email("no-reply@" + SENDER_HOSTNAME, "No Reply")
    personalization.add_to(Email(proper_email(pairing.grader), pairing.grader.name))
    mail.subject = f"Give feedback to {pairing.recipient.name}'s submission"
    if pairing.type == Pairing.IGR:
        mail.subject = f"Give anonymous feedback to {pairing.recipient.name}"
    mail.add_personalization(personalization)
    template_file = get_email_template("new_pairing.html")
    with open(template_file) as f:
        template = jinja2.Template(f.read())
        content = Content(
            "text/html",
            template.render(
                heading=mail.subject,
                discussion_url=discussion_url,
                pairing=pairing,
                hostname=HOSTNAME,
            ),
        )
        mail.add_content(content)

    try:
        response = sg.send(mail)
    except Exception:
        capture_exception()
        return

    if response.status_code >= 400:
        with push_scope() as scope:
            scope.set_extra("response", response)
            capture_message("Email sending failed.")


@rq.job("default")
def send_ta_allocation_email(course_id, assignment_id, ta_id):
    """Send an email to the TA with the list of students that the TA needs to
    review assignments of.

    :param course_id: canvas id of the course
    :param assignment_id: canvas id of the assignment
    :param ta_id: user id of the TA
    """
    ta = User.query.get(ta_id)
    if not ta:
        capture_message(f"Cannot send email to TA. TA with {ta_id} doesn't exist.")
        return

    pairs = (
        Pairing.query.filter(
            Pairing.course_id == course_id,
            Pairing.assignment_id == assignment_id,
            Pairing.grader_id == ta.id,
            Pairing.type == Pairing.TA,
        )
        .options(joinedload(Pairing.recipient))
        .all()
    )

    if not pairs:
        return

    course_name = pairs[0].task.course_name
    assignment_name = pairs[0].task.assignment_name
    mail = Mail()
    personalization = Personalization()
    mail.from_email = Email("notification@" + SENDER_HOSTNAME, "Peer Feedback")
    mail.reply_to = Email("no-reply@" + SENDER_HOSTNAME, "No Reply")
    mail.subject = "Evaluate submissions for assignment: " + assignment_name
    personalization.add_to(Email(proper_email(ta), ta.name))
    mail.add_personalization(personalization)
    template_file = get_email_template("ta_allocation.html")
    with open(template_file) as f:
        template = jinja2.Template(f.read())
        content = Content(
            "text/html",
            template.render(
                heading=mail.subject,
                pairs=pairs,
                hostname=HOSTNAME,
                course_id=course_id,
                assignment_id=assignment_id,
                course_name=course_name,
                assignment_name=assignment_name,
            ),
        )
        mail.add_content(content)

    try:
        response = sg.send(mail)
    except Exception:
        capture_exception()
        return

    if response.status_code >= 400:
        with push_scope() as scope:
            scope.set_extra("response", response)
            capture_message("Email sending failed.")


def send_redo_rubric_emails(fb):
    """Sends the emails to students who have submitted the feedback for an
    assignment whose rubric has been changed

    :param fb: feedback which has been submitted
    """
    mail = Mail()
    personal = Personalization()
    personal.add_to(Email(proper_email(fb.reviewer), fb.reviewer.name))
    mail.add_personalization(personal)
    mail.from_email = Email("notification@" + SENDER_HOSTNAME, "Peer Feedback")
    mail.subject = "Action Required - {0}'s rubric changed".format(fb.assignment_name)
    url = "https://{0}/app/feedback/course/{1}/assignment/{2}/user/{3}/".format(
        HOSTNAME, fb.course_id, fb.assignment_id, fb.receiver_id
    )
    content = f"""Hi {fb.reviewer.name},
    The evaluation rubric for the assignment {fb.assignment_name} in {fb.course_name}
was changed recently. The evaluation you submitted for {fb.receiver.name} needs to be
redone. The comments you have  left for the submission are intact and only the
evaluation in the rubric needs to be redone and submitted again. We have unpublished
your feedback and moved it to drafts. We have also added the task back to your list.

You can find the draft under "You feedback to others" in the assignment page.
Or you can use the link below to submit grades using the new rubric:
{url}

Thank You."""
    mail.add_content(content)
    assert mail.get()
    try:
        response = sg.send(mail)
    except:
        capture_exception()
        return

    if response.status_code >= 400:
        with push_scope() as scope:
            scope.set_extra("response", response)
            capture_message("Email sending failed.")


def send_download_email(user, file_url, course_id, assignment_id=None):
    """Sends the email to the Teacher once the data is ready for download

    :param user: User to whom the report is to be sent
    :param file_url: Download link for the file
    :param course_id: Course ID
    :param assignment_id: Assignment ID
    """
    teacher = get_course_teacher(course_id)
    canvas = get_canvas_client(teacher.canvas_access_token)
    course = canvas.get_course(course_id)
    assignment = course.get_assignment(assignment_id) if assignment_id else None

    mail = Mail()
    mail.from_email = Email("notification@" + SENDER_HOSTNAME, "Peer Feedback")
    mail.reply_to = Email("no-reply@" + SENDER_HOSTNAME, "No Reply")
    personalization = Personalization()
    personalization.add_to(Email(proper_email(user), user.name))
    mail.subject = "Your data export for {0} is ready!".format(course.name)
    if assignment:
        mail.subject = "Your data export for {0} is ready!".format(assignment.name)
    mail.add_personalization(personalization)
    template_file = get_email_template("download_data.html")
    with open(template_file, "r") as f:
        template = jinja2.Template(f.read())
        content = Content(
            "text/html",
            template.render(
                course=course.name,
                assignment=assignment,
                user_name=user.name,
                download_url=file_url,
                hostname=HOSTNAME,
            ),
        )
        mail.add_content(content)

    try:
        response = sg.send(mail)
    except Exception:
        capture_exception()
        return

    if response.status_code >= 400:
        with push_scope() as scope:
            scope.set_extra("response", response)
            capture_message("Email sending failed.")


@rq.job("low")
def send_support_email(user_id, subject, message):
    """Send an Email to the application Administrator from the user.

    :param user_id: user sending the support email
    :param subject: subject of the email
    :param message: contents in the email
    """
    user = User.query.get(user_id)
    if not user:
        return

    sender = Email(user.email, user.name)
    mail = Mail()
    personalization = Personalization()
    personalization.add_to(Email("gabriel@peerfeedback.io", "PeerFeedback Admin"))
    mail.add_personalization(personalization)
    mail.from_email = sender
    mail.reply_to = sender
    mail.subject = subject
    mail.add_content(Content("text/plain", message))

    try:
        response = sg.send(mail)
    except Exception as e:
        capture_exception(e)
        return

    if response.status_code >= 400:
        with push_scope() as scope:
            scope.set_extra("response", response)
            capture_message("Support Email Sending failed")


def send_export_request_received_email(user, course_id, assignment_id=None):
    """Intimate the teacher that the request for data download has been received

    :param user: User to whom the report is to be sent
    :param course_id: Course ID
    :param assignment_id: Assignment ID
    """
    canvas = get_canvas_client(user.canvas_access_token)
    course = canvas.get_course(course_id)
    assignment = None
    if assignment_id:
        assignment = course.get_assignment(assignment_id)

    mail = Mail()
    mail.from_email = Email("notification@" + SENDER_HOSTNAME, "Peer Feedback")
    mail.reply_to = Email("no-reply@" + SENDER_HOSTNAME, "No Reply")
    personalization = Personalization()
    personalization.add_to(Email(proper_email(user), user.name))
    mail.subject = "Your data export request for {0} has been received".format(
        course.name
    )
    if assignment:
        mail.subject = "Your data export request for {0} has been received".format(
            assignment.name
        )

    mail.add_personalization(personalization)
    template_file = get_email_template("export_request_received.html")
    with open(template_file, "r") as f:
        template = jinja2.Template(f.read())
        content = Content(
            "text/html",
            template.render(
                course=course.name,
                user_name=user.name,
                hostname=HOSTNAME,
                assignment=assignment,
            ),
        )
        mail.add_content(content)

    try:
        response = sg.send(mail)
    except Exception:
        capture_exception()
        return

    if response.status_code >= 400:
        with push_scope() as scope:
            scope.set_extra("response", response)
            capture_message("Email sending failed.")


@rq.job("low")
def send_pending_review_reminder(course_id, assignment_id, user_id=None):
    """Send a reminder email to the complete pending reviews of for an assignment.
    If the use id is given, the email is only sent to that user. If the user_id
    is not given, then reminder is sent to all the users who have a pending reviews.

    :param course_id: canvas id of the course
    :param assignment_id: canvas id of the assignment
    :param user_id: user id of the grader who has to be notified
    """
    if user_id:
        user_ids = [user_id]
    else:
        user_ids = (
            db.session.query(Task.user_id)
            .filter(
                Task.course_id == course_id,
                Task.assignment_id == assignment_id,
                Task.status.in_([Task.PENDING, Task.IN_PROGRESS]),
            )
            .distinct()
        )

    users = User.query.filter(User.id.in_(user_ids)).all()
    if not users:
        return

    ref_task = Task.query.filter_by(
        course_id=course_id, assignment_id=assignment_id
    ).first()
    for user in users:
        content = f"""Hi {user.name},

This is a gentle reminder to inform, you still have some reviews pending in
Assignment: {ref_task.assignment_name}
Course: {ref_task.course_name}

You can see the pending items under "Your Feedback to other" section in the following page
https://{HOSTNAME}/app/course/{course_id}/assignment/{assignment_id}

Kindly complete your evaluation in time.

Regards,
PeerFeedback
"""
        mail = Mail(
            from_email="notification@" + SENDER_HOSTNAME,
            to_emails=proper_email(user),
            subject="Reviews pending for assignment " + ref_task.assignment_name,
            plain_text_content=content,
        )
        try:
            response = sg.send(mail)
        except:
            capture_exception()
            return

        if response.status_code >= 400:
            with push_scope() as scope:
                scope.set_extra("response", response)
                capture_message("Sending Reminder Emails failed.", "error")


@rq.job("default")
def send_auto_pairing_notification_to_teachers(course_id, assignment_id):
    """Send an email to the teachers and TAs of the course upon successful
    completion of automatic pairing

    :param course_id: canvas id of the course
    :param assignment_id: canvas id of the assignment
    """
    user_ids = (
        db.session.query(CourseUserMap.user_id)
        .filter(
            CourseUserMap.course_id == course_id,
            (CourseUserMap.role == CourseUserMap.TA)
            | (CourseUserMap.role == CourseUserMap.TEACHER),
        )
        .distinct()
    )
    users = User.query.filter(
        User.id.in_(user_ids), User.settings.has(UserSettings.pairing_emails.is_(True))
    ).all()

    ref_task = Task.query.filter_by(
        course_id=course_id, assignment_id=assignment_id
    ).first()
    subject = "Automatic Pairing complete for " + ref_task.assignment_name
    url = f"https://{HOSTNAME}/app/course/{course_id}/assignment/{assignment_id}/pairing-table"
    template_file = get_email_template("auto_pairing_complete.html")
    with open(template_file) as f:
        template = jinja2.Template(f.read())

    for user in users:
        content = Content(
            "text/html",
            template.render(
                heading=subject,
                user=user.name,
                assignment=ref_task.assignment_name,
                course=ref_task.course_name,
                pairing_table=url,
            ),
        )
        mail = Mail(
            from_email="notification@" + SENDER_HOSTNAME,
            to_emails=proper_email(user),
            subject=subject,
        )
        mail.add_content(content)
        try:
            response = sg.send(mail)
        except:
            capture_exception()
            continue

        if response.status_code >= 400:
            with push_scope() as scope:
                scope.set_extra("response", response)
                capture_message("Sending pairing Notification failed.", "error")
