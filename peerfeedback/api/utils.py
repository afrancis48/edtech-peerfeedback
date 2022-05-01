import random
import dateutil.parser
import csv
import io
import boto3
import logging

from functools import wraps
from datetime import datetime, timezone, timedelta
from canvasapi import Canvas
from flask import request, jsonify
from flask import current_app as app

from flask_jwt_extended import get_current_user, get_jwt_identity, verify_jwt_in_request
from sqlalchemy.orm import joinedload

from peerfeedback.utils import is_valid_email, update_canvas_token
from peerfeedback.extensions import db
from peerfeedback.models import (
    User,
    UserSettings,
    Pairing,
    Feedback,
    Task,
    AssignmentSettings,
    Comment,
    CourseUserMap,
)
from peerfeedback.api import errors

logger = logging.getLogger(__name__)


def generate_review_matches(graders, recipients, rounds):
    """A generator that provides unique peers for reviewing.
    The generated matches follow the following rules:
        1. The no.of reviews/rounds of review is less than total no.of users.
        2. The user won't be reviewing his/her own work
        3. All the reviewers assigned would be unique.
        4. Each user will have equal no.of reviews to give
        5. The users may or may not receive equal no.of reviews

    :param graders: list of ids for whom the matching is to be done.
    :param recipients: list of ids who have submitted the assignments
    :param rounds: The no.of reviews each student is supposed to receive.
    :yields: a tuple of the format (user_index, [index of peers])
    """
    if rounds >= len(graders) or rounds >= len(recipients):
        raise ValueError(
            "No. of reviews cannot be greater than or equal to "
            "the total number of students."
        )

    random.shuffle(recipients)

    for grader in graders:
        if grader in recipients[:rounds]:
            recipients.remove(grader)
            recipients.insert(rounds, grader)
        yield (grader, recipients[:rounds])
        recipients = recipients[rounds:] + recipients[:rounds]


def create_user(canvas_user, save=True):
    """Creates a new user in the DB from the `canvas_user` object passed.
    If a user already exists for matching the Canvas user's ID, then the
    existing user is returned.

    :param canvas_user: Canvas User object
    :param save: Should the user object be saved to the DB immediately after
        being created. Useful for situations when a single object user is
        necessary. Set it to False in situations where multiple users are
        created in a loop and it is better to just create them all first and
        save them in bulk later.
    :return: user object of peerfeedback.user.models.User
    """
    existing = User.query.filter_by(canvas_id=canvas_user.id).first()
    if existing:
        return existing

    profile = canvas_user.get_profile()
    email = profile.get("primary_email", None)
    if not email and hasattr(canvas_user, "email"):
        email = canvas_user.email
    if not email:
        email = profile.get("login_id", "user@example.com")
        if "@" not in email:
            email = email + "@gatech.edu"
    user = User.create(
        avatar_url=profile.get("avatar_url", None),
        bio=profile.get("bio", None),
        canvas_id=profile["id"],
        email=email,
        name=profile["name"],
        username=profile["login_id"],
        real_name=profile["name"],
    )
    UserSettings.create(user=user)
    if save:
        user.save()
    return user


def pairing_exists(grader, recipient, assignment_id):
    """Given two students email and one assignment_id returns true if pairing
    already exists
    """
    return (
            db.session.query(Pairing)
            .filter(Pairing.recipient_id == recipient.id)
            .filter(Pairing.grader_id == grader.id)
            .filter(Pairing.assignment_id == assignment_id)
            .first()
            is not None
    )


def get_email_text_as_list(users):
    """Given a list of user returns their emails"""
    students_emails = []
    for user in users:
        students_emails.append(user.email)

    return students_emails


def filter_students_by_emails(users, students=None):
    """Given a list of user returns which are students"""
    return list(
        filter(lambda user: hasattr(user, "login_id") and user.email in students, users)
    )


def get_canvas_user_by_email(email, student_list):
    """Return the student object with the matching email.

    :param email: email of the student to be found
    :param student_list: list of students. Usually PaginatedList from CanvasAPI
    :return: Student object if email matches, None otherwise
    """
    for student in student_list:
        if getattr(student, "email", "") == email and hasattr(student, "login_id"):
            return student


def get_user_by_email(email, users):
    """Return the user with the matching email from the list of users.

    :param email: email of the user
    :param users: list of User objects
    :return: User object with the matching email
    """
    for user in users:
        if user.email == email:
            return user


def get_user_by_username(username, users):
    """Return the user with the matching username (login_id) from the list of users.

    :param email: username (login_id) of the user
    :param users: list of User objects
    :return: User object with the matching username (login_id)
    """
    for user in users:
        if user.username == username:
            return user


def create_pairing(
        creator,
        grader,
        recipient,
        course,
        assignment,
        pair_type=Pairing.STUDENT,
        study=None,
        pseudo_name=None,
        view_only=None
):
    """Create a new Pairing object  with the inputs, and assign task to the
    grader

    :param creator: User object of the person creating the pairings
    :param grader: User object to be assigned the grading task
    :param recipient: User object whose assignment is to be graded
    :param course: the canvas Course object
    :param assignment: the canvas assignment object
    :param view_only:
    :param pair_type: the type of the pairing, refer Pairing model for types
    :param study: an object of model Study
    :param pseudo_name: value for the pseudo name attribute of the pairing model
    :return: the created pairing object
    """
    settings = AssignmentSettings.query.filter_by(assignment_id=assignment.id).first()
    if not settings:
        raise errors.CourseNotSetup()

    if view_only is None:
        view_only = False

    existing = Pairing.query.filter_by(
        grader_id=grader.id,
        recipient_id=recipient.id,
        assignment_id=assignment.id,
        course_id=course.id,
        archived=False,
        view_only=False
    ).first()
    if existing and view_only is not None:
        raise errors.PairingExists()

    if grader.id == recipient.id or grader.canvas_id == recipient.canvas_id:
        raise errors.PairingToSelf()

    pairing = Pairing.create(
        type=pair_type,
        grader_id=grader.id,
        recipient_id=recipient.id,
        course_id=course.id,
        assignment_id=assignment.id,
        creator_id=creator.id,
        view_only=view_only
    )
    if study and pseudo_name:
        pairing.study = study
        pairing.pseudo_name = pseudo_name
    pairing.save()

    due_date = None
    if assignment.due_at:
        if settings.deadline_format == "canvas" and settings.feedback_deadline:
            due_date = dateutil.parser.parse(assignment.due_at) + timedelta(
                days=settings.feedback_deadline
            )
        elif settings.deadline_format == "custom" and settings.custom_deadline:
            due_date = settings.custom_deadline

    task = Task.create(
        status=Task.PENDING,
        course_id=course.id,
        course_name=course.name,
        assignment_id=assignment.id,
        assignment_name=assignment.name,
        user_id=grader.id,
        pairing_id=pairing.id,
        due_date=due_date,
        view_only=view_only
    )
    task.save()

    feedback = Feedback.create(
        type=pair_type,
        draft=True,
        assignment_name=assignment.name,
        assignment_id=assignment.id,
        course_name=course.name,
        course_id=course.id,
        read_time=0,
        write_time=0,
        grades=[],
        receiver_id=recipient.id,
        reviewer_id=grader.id,
        pairing_id=pairing.id,
        rubric_id=settings.rubric_id,
    )
    feedback.save()

    return pairing


def emails_are_not_valid(all_emails):
    return False in [is_valid_email(email) for email in all_emails]


def get_course_teacher(course_id):
    """Function that finds the teacher in the DB for the given course so that
    things like fetching the submissions can be done for other users.

    :param course_id: canvas course id
    :return: teacher object of class `peerfeedback.users.models.User` or None
        if no teacher associated with a particular course is found
    """
    teacher_maps = (
        CourseUserMap.query.filter(CourseUserMap.course_id == course_id)
            .filter(CourseUserMap.role == CourseUserMap.TEACHER)
            .all()
    )
    teacher = next(
        (t.user for t in teacher_maps if t.user.canvas_expiration_time), None
    )

    twenty_minutes_forward = datetime.now(tz=timezone.utc) + timedelta(minutes=20)
    if teacher and twenty_minutes_forward > teacher.canvas_expiration_time:
        update_canvas_token(teacher)

    return teacher


def get_canvas_client(canvas_token=None):
    if not canvas_token:
        user = get_current_user()
        canvas_token = user.canvas_access_token

    return Canvas(app.config.get("CANVAS_API_URL"), canvas_token)


def post_reply_to_comment(old_id, user_email, content):
    """Creates a new comment object using the given information

    :param old_id: (int) id of the `Comment` to which this is new comment is a reply
    :param user_email: email of the user posting the comment
    :param content: comment content
    """
    old = Comment.query.get(old_id)
    user = User.query.filter_by(email=user_email).first()

    if not old or not user:
        return

    comment = Comment.create(
        course_id=old.course_id,
        course_name=old.course_name,
        assignment_id=old.assignment_id,
        assignment_name=old.assignment_name,
        submission_id=old.submission_id,
        commenter_id=user.id,
        recipient_id=old.recipient_id,
        value=content,
    )
    comment.save()


def post_comment_to_feedback(feedback_id, user_email, content):
    """Creates a new comment object using given information

    :param feedback_id: id of the feedback to which the comment is made
    :param user_email: email of the user making the comment
    :param content: comment content
    """
    feedback = Feedback.query.get(feedback_id)
    user = User.query.filter_by(email=user_email).first()

    if not feedback or not user:
        return

    comment = Comment.create(
        course_id=feedback.course_id,
        course_name=feedback.course_name,
        assignment_id=feedback.assignment_id,
        assignment_name=feedback.assignment_name,
        submission_id=feedback.submission_id,
        commenter_id=user.id,
        recipient_id=feedback.reviewer_id,
        value=content,
    )
    comment.save()


def assign_students_to_tas(allotment, students):
    """Function that maps the students to the TAs according to the provided
    allotment

    :param allotment: a list of dict(id, student_count)
    :param students: list of student ids
    :return: list of dict(ta_id, student_count, student_ids:list))
    """
    total_allotted = sum([a["student_count"] for a in allotment])
    if total_allotted != len(students):
        raise ValueError("Allotted student count does not match available students")

    random.shuffle(students)

    start = 0
    for allot in allotment:
        count = int(allot["student_count"])
        allot["student_ids"] = students[start: start + count]
        start += count

    return allotment


def get_db_users(users, create_missing):
    """Given a list of canvas users, check the database for the existing ones
    and add the ones that are missing

    :param users: Canvas api users
    :param create_missing: boolean to indicate if missing are to be created
    :return: list of the users from the database
    """
    canvas_ids = [u.id for u in users]
    existing = User.query.filter(User.canvas_id.in_(canvas_ids)).all()

    if len(canvas_ids) == len(existing) or not create_missing:
        return existing

    existing_ids = [u.canvas_id for u in existing]
    new_users = [
        create_user(user, False) for user in users if user.id not in existing_ids
    ]
    db.session.add_all(new_users)
    db.session.commit()
    return existing + new_users


def fetch_emailable_users(user_ids, email_type):
    """Return a list of email-able users based on their preferences

    :param user_ids: list of user ids
    :param email_type: string denoting if the email is either comment, feedback,
        of discussion
    :return: list of `User` objects
    """
    query = (
        db.session.query(UserSettings)
            .filter(UserSettings.user_id.in_(user_ids))
            .options(joinedload(UserSettings.user))
    )

    if email_type == "comment":
        query = query.filter(UserSettings.comment_emails.is_(True))
    elif email_type == "feedback":
        query = query.filter(UserSettings.feedback_emails.is_(True))
    elif email_type == "discussion":
        query = query.filter(UserSettings.discussion_emails.is_(True))

    emailable_users = [setting.user for setting in query.all()]
    # Just in case the user settings wasn't created for the user - ideally none
    # non_logged_in = (
    #     db.session.query(User)
    #     .filter(User.settings.is_(None), User.id.in_(user_ids))
    #     .all()
    # )

    # return emailable_users + [user for user in non_logged_in]
    return emailable_users


def user_is_ta_or_teacher(user, course_id, course=None):
    """Function that checks if the given user is a teacher or TA for the course

    :param user: user object of type peerfeedback.user.model.User
    :param course_id: id of the canvas course
    :param course: course object of the CanvasAPI obtained using the canvas client
    :return: true to specify if the user is either TA or teacher
    """
    maps = CourseUserMap.query.filter(
        CourseUserMap.user_id == user.id, CourseUserMap.course_id == course_id
    ).all()
    if maps:
        roles = [m.role for m in maps]
        return CourseUserMap.TEACHER in roles or CourseUserMap.TA in roles

    # If nothing is found in the mapping, then use the Canvas API
    # Situations like users access the app before Teacher initializes course
    if not course:
        canvas = get_canvas_client(user.canvas_access_token)
        course = canvas.get_course(course_id)

    enrollments = course.get_enrollments(user_id=user.canvas_id)
    if not enrollments:
        return False
    enrolls = [e.type for e in enrollments]
    return "TeacherEnrollment" in enrolls or "TaEnrollment" in enrolls


def allowed_roles(*args):
    """Decorator factory to establish access control.

    The decorator gets the user's role based on the course_id accessed through
    the view functions arguments, and returns the function if the roles
    match the allowed roles, and returns 403 error if they don't.

    In case the decorator is used on a function that doesn't have the course id
    as one of its parameters, then it just returns the function without
    modification
    """
    acceptable_roles = list(args)

    def decorator(fn):
        """Decorator that enforces the access rights"""

        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()

            _json = request.get_json()
            if "course_id" not in request.view_args and "course_id" not in _json:
                return fn(*args, **kwargs)

            course_id = request.view_args.get("course_id", None) or _json.get(
                "course_id"
            )
            identity = get_jwt_identity()
            course_map = CourseUserMap.query.filter(
                CourseUserMap.course_id == course_id,
                CourseUserMap.user_id == identity["id"],
            ).first()

            if not course_map:
                msg = errors.COURSE_NOT_SETUP + " or " + errors.NOT_ENROLLED
                return jsonify(dict(message=msg)), 400

            if course_map.role not in acceptable_roles:
                return jsonify(dict(message=errors.NOT_AUTHORISED)), 403
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def make_csv(rows, heading):
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(heading)
    cw.writerows(rows)
    return si


def upload_file_to_s3(file_obj, name):
    s3 = boto3.client(
        "s3",
        aws_access_key_id=app.config.get("S3_KEY"),
        aws_secret_access_key=app.config.get("S3_SECRET"),
    )

    bucket_name = app.config.get("S3_BUCKET")

    s3.put_object(
        Bucket=bucket_name,
        Key=name,
        Body=file_obj.getvalue(),
        ContentType="application/csv",
    )

    url = s3.generate_presigned_url(
        ClientMethod="get_object", Params={"Bucket": bucket_name, "Key": name}
    )

    return url


def proper_email(user):
    """Checks the email field of the user and returns a usable email for the
    user.

    :param user: User object
    :return: email string with @ and gatech.edu present
    """
    if not user:
        raise ValueError("user cannot be None")
    if not user.email:
        return user.username + "@gatech.edu"
    if not "@" in user.email:
        return user.email + "@gatech.edu"
    return user.email


def auth_header(user):
    return {"Authorization": "Bearer " + user.canvas_access_token}


def required_params(*args):
    """Decorator factory to check request data for POST requests and return
    an error if required parameters are missing."""
    required = list(args)

    def decorator(fn):
        """Decorator that checks for the required parameters"""

        @wraps(fn)
        def wrapper(*args, **kwargs):
            missing = [r for r in required if r not in request.get_json()]
            if missing:
                response = {
                    "status": "error",
                    "message": errors.MISSING_PARAMS,
                    "missing": missing,
                }
                return jsonify(response), 400
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def generate_non_group_pairs(groups, recipients, rounds):
    """Algorithm to create pairing without any student getting paired with
    another student from the same group. This algorithm follows all the rules
    of `generate_review_matches` with an extra rule:
        - A student cannot be paired to another student from the same group

    :param groups: a dictionary of group ids as keys and a list of grader ids
        as values
    :param recipients: a list of user IDs who are to be assigned as peers to
        the graders
    :param rounds: the no.of peers a grader should be assigned for review
    :returns: a dictionary of graders and a list of peers who are assigned to
        them
    """
    # Create a map of how many times a user is assessed. This will help in
    # prioritising those who receive least amount of reviews to be picked first
    if not groups:
        logger.error("Cannot generate Group based pairs. Groups empty.")
        raise Exception(
            "There are no groups to generate non-groups pairs. Use "
            "`generate_review_matches` instead."
        )

    if not recipients:
        logger.error("Cannot generate group based pairs. Recipients empty.")
        raise Exception("There are no recipients to pair.")

    assessed = {user: 0 for user in recipients}
    pairing = {user: [] for gid in groups for user in groups[gid]}

    # The actual algorithm involves a factor of randomness for shuffling the
    # students so that Group A doesn't get matched to Group B directly. This
    # randomness also results in some student being left out without any reviews
    # under rare conditions. This while loop ensures that everyone is assessed
    while not all(assessed.values()):
        group_list = [gid for gid in groups]
        # user -> group lookup table
        group_of = {user: gid for gid in groups for user in groups[gid]}
        # Keep track of how many students have been selected from the group
        chosen_from_group = {gid: 0 for gid in groups}
        assessed = {user: 0 for user in recipients}

        # The actual pairing logic. Move group by group, assigning pairs to
        # each student in the group.
        while len(group_list):
            # By choosing the groups who are reviewed the least and assigning them
            # reviewers first, we increase the chance of this group being picked in
            # the next round
            group_list.sort(key=lambda g: chosen_from_group[g])
            current_group = group_list.pop(0)
            graders = groups[current_group]
            available = [s for s in recipients if s not in graders]
            for grader in graders:
                # sort the available students such that the ones who aren't
                # reviewed gets preferred. In case the reviews are the same,
                # then just randomize their position.
                available.sort(key=lambda s: (assessed[s], random.randint(1, 10)))
                peers = available[:rounds]
                pairing[grader] = peers
                for peer in peers:
                    chosen_from_group[group_of[peer]] += 1
                    assessed[peer] += 1
    return pairing


def validate_csv_input(course_id, pairs, grader_type):
    """Validates the input for the CSV pairing

    :param course_id: canvas course id
    :param pairs: the pairs JSON sent by the client
    :param grader_type: the type of the grader "STUDENT" or "TA"
    :return: dictionary of the validation status and message
    """
    if type(pairs) is not list:
        return {"status": "error", "message": errors.INVALID_DATA_FORMAT}

    properly_formatted = all(["grader" in p and "recipients" in p for p in pairs])
    if not properly_formatted:
        return {"status": "error", "message": errors.INVALID_DATA_FORMAT}
    requested_students = []
    requested_tas = []

    # include the graders in the student list when type is student
    if grader_type == "STUDENT":
        requested_students = [pair["grader"] for pair in pairs]
    else:
        requested_tas = [pair["grader"] for pair in pairs]

    for pair in pairs:
        requested_students.extend(pair["recipients"])
    requested_students = list(set(requested_students))

    teacher = get_course_teacher(course_id)
    canvas = get_canvas_client(teacher.canvas_access_token)
    course = canvas.get_course(course_id)
    students = course.get_users(
        include=["email", "login_id"],
        enrollment_type=["student"],
        enrollment_state=["active"],
    )
    tas = []
    if grader_type == "TA":
        tas = course.get_users(
            include=["email", "login_id"],
            enrollment_type=["ta"],
            encollement_state=["active"],
        )

    course_usernames = []
    course_ids = []
    for student in students:
        course_usernames.append(student.login_id)
        course_ids.append(student.id)

    non_course_usernames = [
        name for name in requested_students if name not in course_usernames
    ]

    if non_course_usernames:
        return {
            "status": "error",
            "message": errors.SOME_IDS_NOT_IN_COURSE
                       + " Check if you have set the right grader type. Missing Ids: "
                       + " ".join(non_course_usernames),
        }

    if grader_type == "TA":
        course_ta_usernames = []
        for ta in tas:
            course_ta_usernames.append(ta.login_id)
            course_ids.append(ta.id)
        non_course_tas = [
            name for name in requested_tas if name not in course_ta_usernames
        ]
        if non_course_tas:
            return {
                "status": "error",
                "message": errors.SOME_IDS_NOT_IN_COURSE
                           + " Check if you have set the right grader type. Missing Ids: "
                           + " ".join(non_course_tas),
            }
        else:
            course_usernames.extend(course_ta_usernames)

    return {
        "status": "success",
        "course_ids": course_ids,
        "course_usernames": course_usernames,
        "students": students,
        "course": course,
    }
