"""
File that contains cron like jobs that need to be run for things like system
maintenance
"""
import datetime
import json
import logging
from collections import defaultdict
from datetime import timedelta, timezone

import jinja2
import requests
from dateutil.parser import parse as parse_date
from sendgrid.helpers.mail import Content, Mail
from sentry_sdk import capture_exception, capture_message, push_scope
from sqlalchemy.sql import func

from peerfeedback.api.jobs.pairing import pair_automatically
from peerfeedback.api.jobs.sendmail import (HOSTNAME, SENDER_HOSTNAME,
                                            get_email_template, sg)
from peerfeedback.api.utils import (get_canvas_client, get_course_teacher,
                                    proper_email)
from peerfeedback.extensions import db, rq
from peerfeedback.models import (Feedback, JWTToken, MetaFeedback, Pairing,
                                 Task, User)
from peerfeedback.settings import Config

logger = logging.getLogger(__name__)


@rq.job("default")
def clear_expired_tokens():
    now = datetime.datetime.now()
    expired_tokens = JWTToken.query.filter(JWTToken.expires < now).all()
    for token in expired_tokens:
        token.delete()


@rq.job("low", timeout=60 * 30)
def award_ml_grade(num=250, course_id=None):
    query = Feedback.query.filter(
        Feedback.ml_rating.is_(None),
        Feedback.value.isnot(None),
        Feedback.draft.is_(False),
    )

    if course_id:
        query = query.filter(Feedback.course_id == course_id)

    fbs = query.limit(num).all()

    if len(fbs) == 0:
        return

    url = Config.MLAPP_URL + "/batch-grade-feedback/"
    index = 0
    batch_amount = 120
    batch = batch_amount
    count = len(fbs)
    while index < count:
        selected = fbs[index:batch]
        index += batch_amount
        batch = index + batch_amount
        txts = [fb.value for fb in selected]
        res = requests.post(url, json={"texts": txts})

        if res.status_code != 200:
            logger.error(
                "Did not get ML score from ML app. Status: %d", res.status_code
            )
            logger.debug(res.content)
            continue

        predictions = json.loads(res.content)

        for fb, preds in zip(selected, predictions):
            assert len(preds) == 2
            fb.ml_rating = preds[0]
            fb.ml_prob = preds[1]
            db.session.add(fb)

    db.session.commit()


@rq.job("default")
def update_pairing_schedules():
    """Cron job that checks if all the scheduled auto pairing jobs are in sync
    with their assignment due dates set in the canvas. If the due date has been
    removed, the job is cancelled. If the due_date has been changed, then the
    job is rescheduled to run 1 hr after the new due date.
    """
    scheduler = rq.get_scheduler()
    jobs = scheduler.get_jobs(with_times=True)
    logger.info("Updating Pairing schedules. Syncing with assignment due dates")

    for job, scheduled_time in jobs:
        if "pair_automatically" not in job.func_name or job.origin == "scheduled":
            logger.debug(f"Skipping {job.func_name}")
            continue
        course_id, assignment_id, rounds, uid, ex_def, ex_students, email = job.args
        teacher = get_course_teacher(course_id)
        canvas = get_canvas_client(teacher.canvas_access_token)
        course = canvas.get_course(course_id)
        assignment = course.get_assignment(assignment_id)

        if not assignment.due_at:
            logger.info(
                f"Cancelling job for assignment {assignment.name} as due_at is empty"
            )
            scheduler.cancel(job)
            continue

        due_at = parse_date(assignment.due_at).astimezone(timezone.utc)
        expected_schedule = due_at.replace(tzinfo=None) + timedelta(hours=1)
        if scheduled_time == expected_schedule:
            logger.debug(
                f"Not changing the schedule for assignment #{assignment.id} {assignment.name}"
            )
            continue
        scheduler.cancel(job)
        pair_automatically.schedule(
            expected_schedule,
            course_id,
            assignment_id,
            rounds,
            uid,
            ex_def,
            ex_students,
            email,
            timeout=60 * 30,
        )
        logger.info(
            f"Schedule for assignment #{assignment.id} {assignment.name} changed to {expected_schedule.isoformat()}"
        )


@rq.job("low")
def anonymize_users():
    """Anonymize users who haven't logged into the system for more than 2 years.
    Empty the following fields:
    1. avatar_url
    2. name
    3. real_name
    """
    two_yrs_ago = datetime.datetime.now() - timedelta(days=730)

    # We can deduce the user's last login by checking the updated on date, as
    # every time the user logs in the canvas access token and expiry time would
    # have been updated too, which in turn will affect the updated_on date
    users = User.query.filter(User.updated_on < two_yrs_ago).all()
    for user in users:
        user.name = ""
        user.real_name = ""
        user.avatar_url = ""
        db.session.add(user)
    db.session.commit()
    logger.info(f"Anonymized {len(users)} users")


@rq.job("cron", timeout=60 * 500)
def update_user_reputation():
    """Calculates the feedback metrics of a student. The following fields of
    the user model are updated in this cron job:

    1. feedback_given - No of feedback that the user has completed
    2. reputation - The average rating he has received for those feedback
    3. oldest_review - The oldest review the user has given
    """
    last_year = datetime.datetime.now() - timedelta(days=365)
    students = User.query.filter(User.canvas_expiration_time > last_year).all()

    for student in students:
        fb = (
            Feedback.query.filter(
                Feedback.draft.is_(False), Feedback.reviewer_id == student.id
            )
            .order_by(Feedback.end_date)
            .first()
        )
        student.oldest_review = fb.end_date if fb else None

        count = Feedback.query.filter(
            Feedback.reviewer_id == student.id,
            Feedback.draft.is_(False),
            Feedback.pairing.has(Pairing.archived.is_(False)),
        ).count()
        student.feedback_given = count

        score = (
            MetaFeedback.query.with_entities(
                func.avg(MetaFeedback.points).label("average")
            )
            .filter(MetaFeedback.receiver_id == student.id)
            .scalar()
        )
        student.reputation = float(score) if score else 0

        student.save()


def send_reminder_emails_for_unfinished_tasks():
    """Sends out emails to  students who haven't finished all their reviews.
    It shall happen four and a half days before the deadline. The deadline can
    be either custom or based on canvas submission deadline. The reminder email
    should be sent in both cases.
    """
    logger.info("Starting Task: Send reminder emails for unfinished tasks")
    now = datetime.datetime.now()
    after_4_days = now + datetime.timedelta(days=4)
    after_5_days = now + datetime.timedelta(days=5)
    pending_users = (
        db.session.query(Task.user_id, db.func.count(Task.id))
        .filter(
            Task.due_date < after_5_days,
            Task.due_date > after_4_days,
            Task.status.in_([Task.PENDING, Task.IN_PROGRESS]),
        )
        .group_by(Task.user_id)
    )

    template_file = get_email_template("pending_tasks.html")
    with open(template_file) as f:
        template = jinja2.Template(f.read())

    total = 0
    succeeded = 0
    failed = 0

    for user_id, pending_tasks in pending_users:
        user = User.query.get(user_id)
        logger.debug(f"Sending reminders to {user}")
        tasks = Task.query.filter(
            Task.user_id == user_id,
            Task.due_date < after_5_days,
            Task.due_date > after_4_days,
            Task.status.in_([Task.PENDING, Task.IN_PROGRESS]),
        ).all()
        assignment_tasks = defaultdict(list)
        for task in tasks:
            assignment_tasks[task.assignment_id].append(task)

        for aid, a_tasks in assignment_tasks.items():
            total += 1
            count = len(a_tasks)
            assignment = a_tasks[0].assignment_name
            cid = a_tasks[0].course_id
            course = a_tasks[0].course_name
            due = a_tasks[0].due_date
            mail = Mail(
                from_email="notification@" + SENDER_HOSTNAME,
                to_emails=proper_email(user),
                subject=f"Alert! {count} feedback tasks pending in {assignment}",
            )
            url = f"https://{HOSTNAME}/app/course/{cid}/assignment/{aid}"
            content = Content(
                "text/html",
                template.render(
                    pending_count=count,
                    user=user.name,
                    assignment=assignment,
                    course=course,
                    due_date=due,
                    url=url,
                    hostname=HOSTNAME,
                ),
            )
            mail.add_content(content)
            try:
                logger.debug(f"Mailing user #{user.id} for assignment #{aid}")
                response = sg.send(mail)
            except:
                logger.warning(
                    f"Email FAILED for user #{user.id} for assignment #{aid}"
                )
                failed += 1
                capture_exception()
                continue

            if response.status_code >= 400:
                logger.warning(
                    f"Email FAILED for user #{user.id} for assignment #{aid}"
                )
                failed += 1
                with push_scope() as scope:
                    scope.set_extra("sendgrid_response", response)
                    capture_message("Sending Pending Alert Failed", "error")
            else:
                succeeded += 1
    logger.info("Completed sending reminder emails for pending tasks")
    logger.info(f"Total: {total}    Succeeded: {succeeded}  Failed: {failed}")
