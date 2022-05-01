import requests
from canvasapi.exceptions import Unauthorized, ResourceDoesNotExist
from flask import jsonify, request, Response
from flask_jwt_extended import jwt_required, get_current_user
from sqlalchemy import text
from sqlalchemy.orm import joinedload

from peerfeedback.api import errors
from peerfeedback.api.jobs.course import import_course_information
from peerfeedback.api.schemas import real_user_schema, user_schema
from peerfeedback.api.schemas import CourseSchema, AssignmentSchema, SubmissionSchema
from peerfeedback.api.utils import (
    get_canvas_client,
    user_is_ta_or_teacher,
    allowed_roles,
    get_course_teacher,
    get_db_users,
    pairing_exists,
)
from peerfeedback.api.views import api_blueprint
from peerfeedback.extensions import db, cache
from peerfeedback.models import AssignmentSettings, Task, Pairing, User, CourseUserMap

CACHE_TIMEOUT = 60 * 60 * 12


@api_blueprint.route("/courses/")
@jwt_required
def get_courses():
    """Get the courses of the user

    :return: JSON of the user's courses
    """
    user = get_current_user()
    canvas = get_canvas_client(user.canvas_access_token)
    try:
        courses = canvas.get_courses(
            include=["term", "course_image", "public_description"],
            state=["available", "completed"],
        )
        return jsonify(CourseSchema().dump(courses, many=True))
    except Exception as e:
        return jsonify({"message": errors.CANVAS_ERROR + " " + str(e)}), 500


@api_blueprint.route("/course/<int:course_id>/")
@jwt_required
def get_course(course_id):
    """Get a specific course from Canvas

    :param course_id: Canvas ID of the course
    :return: JSON of the course
    """
    user = get_current_user()

    canvas = get_canvas_client(user.canvas_access_token)
    try:
        course = canvas.get_course(course_id, include=["public_description", "term"])
        return jsonify(CourseSchema().dump(course))
    except Exception as e:
        return jsonify({"message": errors.CANVAS_ERROR + " " + str(e)}), 500


@api_blueprint.route("/course/<int:course_id>/assignments/")
@jwt_required
def get_assignments(course_id):
    """Get the assignments of a particular course from Canvas

    :param course_id: canvas id of the course
    :return: list of assignments in the course
    """
    user = get_current_user()
    try:
        teacher_or_ta = user_is_ta_or_teacher(user, course_id)
    except Unauthorized:
        return jsonify({"message": errors.NOT_ENROLLED}), 400

    canvas = get_canvas_client(user.canvas_access_token)
    course = canvas.get_course(course_id)
    assignments = course.get_assignments()
    if teacher_or_ta:
        settings = AssignmentSettings.query.filter(
            AssignmentSettings.assignment_id.in_([a.id for a in assignments])
        ).all()
        igrs = [s.assignment_id for s in settings if s.intra_group_review]
        adicts = AssignmentSchema().dump(assignments, many=True)
        for adict in adicts:
            adict["intra_group_review"] = adict["id"] in igrs
        return jsonify(adicts)

    # if the use is a student, show only the assignments activated in
    # the peer feedback app by the teacher
    ids = [assignment.id for assignment in assignments]
    sql = text(
        "SELECT DISTINCT assignment_id FROM pairing WHERE assignment_id IN :id_list"
    )
    pairing_done = db.engine.execute(sql, id_list=tuple(ids)).fetchall()
    activated_ids = [i[0] for i in pairing_done]

    settings = (
        db.session.query(AssignmentSettings)
        .filter(
            AssignmentSettings.assignment_id.in_(activated_ids)
            | (
                AssignmentSettings.assignment_id.in_(ids)
                & AssignmentSettings.allow_student_pairing.is_(True)
            )
        )
        .all()
    )
    student_pairing_enabled = [a.assignment_id for a in settings]
    igrs = [a.assignment_id for a in settings if a.intra_group_review]
    assigns = [a for a in assignments if a.id in student_pairing_enabled]
    assignment_dicts = AssignmentSchema().dump(assigns, many=True)
    for adict in assignment_dicts:
        adict["intra_group_review"] = adict["id"] in igrs
    return jsonify(assignment_dicts)


@api_blueprint.route("/course/<int:course_id>/assignment/<int:assignment_id>/")
@jwt_required
@cache.memoize(timeout=CACHE_TIMEOUT)
def get_assignment(course_id, assignment_id):
    """Get a particular assignment from canvas

    :param course_id: canvas course id
    :param assignment_id: canvas assignment id
    :return: JSON of the assignment object
    """
    user = get_current_user()

    try:
        teacher_or_ta = user_is_ta_or_teacher(user, course_id)
    except Unauthorized:
        return jsonify({"message": errors.NOT_ENROLLED}), 400

    if not teacher_or_ta:
        settings = AssignmentSettings.query.filter_by(
            assignment_id=assignment_id
        ).first()
        if not settings:
            return jsonify({"message": "Assignment not present in the app."}), 404

        canvas_user = user
        teacher = get_course_teacher(course_id)

        if teacher:
            canvas_user = teacher

        canvas = get_canvas_client(canvas_user.canvas_access_token)
        course = canvas.get_course(course_id)
        assignment = course.get_assignment(assignment_id)

    canvas = get_canvas_client(user.canvas_access_token)
    course = canvas.get_course(course_id)
    assignment = course.get_assignment(assignment_id)
    return jsonify(AssignmentSchema().dump(assignment))


@api_blueprint.route("/course/<int:course_id>/students/")
@allowed_roles("teacher", "ta")
def get_students(course_id):
    """Get the list of students who are enrolled in the course

    :param course_id: canvas course id
    :return: list of students in the course
    """
    teacher = get_course_teacher(course_id)
    canvas = get_canvas_client(teacher.canvas_access_token)
    course = canvas.get_course(course_id)
    students = course.get_users(
        include=["email"], enrollment_type=["student"], enrollment_state=["active"]
    )
    student_list = [
        dict(name=s.name, email=getattr(s, "email", ""), id=s.id, user_id=s.login_id)
        for s in students
    ]
    return jsonify(student_list)


@api_blueprint.route("/course/<int:course_id>/tas/")
@allowed_roles("teacher", "ta")
def get_tas(course_id):
    """Get the list of TAs who are assigned to the course

    :param course_id: The canvas course id
    :return: list of user objects for the TAs in the course
    """
    teacher = get_course_teacher(course_id)
    canvas = get_canvas_client(teacher.canvas_access_token)
    course = canvas.get_course(course_id)
    tas = course.get_users(
        include=["email"], enrollment_type=["ta"], enrollment_state=["active"]
    )
    ta_list = [
        dict(
            name=t.name,
            email=getattr(t, "email", ""),
            id=t.id,
            user_id=getattr(t, "login_id", ""),
        )
        for t in tas
    ]
    return jsonify(ta_list)


@api_blueprint.route("/course/<int:course_id>/assignment/<int:assignment_id>/tas/")
@allowed_roles("teacher", "ta")
def get_paired_tas(course_id, assignment_id):
    """Get the list of TAs for the course along with the count of assigned
    students for review.

    POST - start the allocation job which will assign given number of students
            to the TAs for review.

    :param course_id: canvas id of the course
    :param assignment_id: canvas id of the assignment
    :return:
    """
    teacher = get_course_teacher(course_id)
    if not teacher:
        return jsonify({"message": errors.CANNOT_FIND_TEACHER}), 503

    canvas = get_canvas_client(teacher.canvas_access_token)
    course = canvas.get_course(course_id)
    tas = course.get_users(enrollment_type=["ta"])
    ta_users = get_db_users(tas, create_missing=True)
    tasks = (
        db.session.query(Task.user_id, Task.status)
        .filter(
            Task.user_id.in_([u.id for u in ta_users]),
            Task.course_id == course_id,
            Task.assignment_id == assignment_id,
            Task.pairing.has(Pairing.type == Pairing.TA),
        )
        .all()
    )

    ta_dicts = []
    for user in ta_users:
        user_dict = real_user_schema.dump(user)
        user_dict["assigned"] = sum(1 for t in tasks if t.user_id == user.id)
        user_dict["completed"] = sum(
            1 for t in tasks if t.user_id == user.id and t.status == Task.COMPLETE
        )
        ta_dicts.append(user_dict)

    return jsonify(ta_dicts)


@api_blueprint.route(
    "/course/<int:course_id>/assignment/<int:assignment_id>/user/<int:user_id>/"
)
@allowed_roles("student", "teacher", "ta")
@cache.memoize(timeout=CACHE_TIMEOUT)
def get_submission(course_id, assignment_id, user_id):
    """Get the submission of a user for an assignment

    :param course_id: canvas id of the course
    :param assignment_id: canvas id of the assignment
    :param user_id: id of the user whose submission is to be returned
    :return: submission dictionary as JSON
    """
    teacher = get_course_teacher(course_id)
    if not teacher:
        return jsonify({"message": errors.COURSE_NOT_SETUP}), 400

    current_user = get_current_user()
    recipient = User.query.get(user_id)
    if not (
        current_user.id == user_id
        or user_is_ta_or_teacher(current_user, course_id)
        or pairing_exists(current_user, recipient, assignment_id)
    ):
        return jsonify({"message": "You are not allowed to view this submission"}), 403

    canvas = get_canvas_client(teacher.canvas_access_token)
    course = canvas.get_course(course_id)
    assignment = course.get_assignment(assignment_id)
    try:
        sub = assignment.get_submission(
            recipient.canvas_id, include=["assignment", "course"]
        )
    except ResourceDoesNotExist:
        return jsonify({"message": "Submission not found"}), 404

    # Override the user information with local user
    submission = SubmissionSchema().dump(sub)
    submission["user_id"] = recipient.id
    submission["user"] = user_schema.dump(recipient)

    pairing = (
        Pairing.query.filter(
            Pairing.grader == current_user,
            Pairing.recipient == recipient,
            Pairing.assignment_id == assignment_id,
        )
        .options(joinedload(Pairing.task))
        .first()
    )

    if pairing and pairing.study_id and pairing.task.status != Task.COMPLETE:
        submission["user"]["name"] = pairing.pseudo_name
        submission["user"]["avatar_url"] = ""

    if getattr(sub, "attachments", None):
        settings = AssignmentSettings.query.filter_by(
            assignment_id=assignment_id
        ).first()
        if settings.filter_pdf:
            submission["attachments"] = [
                a for a in sub.attachments if a["content-type"] == "application/pdf"
            ]
        else:
            submission["attachments"] = sub.attachments

    return jsonify(submission)


@api_blueprint.route("/pdf/")
def get_pdf():
    """Function that gets the pdf file from canvas and streams it to the client"""

    # Note: When testing with the current docker setup, the request FAILS
    # as when requesting the http://canvas/ url, it creates a redirect to
    # http://localhost/ (it's public URL)
    #
    # In a production environment where public DNS is employed, the redirects
    # should work fine and the PDF should be streamed.

    pdf_url = request.args.get("url")
    resp = requests.get(pdf_url, stream=True)
    return Response(resp.content, mimetype="application/pdf")


@api_blueprint.route("/course/<int:course_id>/initialize/", methods=["POST"])
@jwt_required
def initialize_course(course_id):
    """View that would start a background job to import the course data from
    Canvas into Peer Feedback app.

    :param course_id: the id of the canvas course
    :return: the job id of the background job
    """
    user = get_current_user()
    canvas = get_canvas_client(user.canvas_access_token)
    course = canvas.get_course(course_id)
    enrollments = course.get_enrollments(user_id=user.canvas_id)
    if "TeacherEnrollment" not in [e.type for e in enrollments]:
        return jsonify({"message": errors.ONLY_TEACHERS}), 403
    job = import_course_information.queue(course_id, user.id)
    return jsonify(dict(id=job.id))


@api_blueprint.route("/course/<int:course_id>/retry/")
@jwt_required
def retry_fetching_submission(course_id):
    """This function would be called when a student cannot see an assignment in
    the review page. One of the reasons why that might happen is that he (the grader)
    might not be in the Course UserMap table as he might not have been enrolled
    in the course when the course was initialized. So the @allowed_roles
    decorator cannot find the user's role and deny him the submission information.

    Then the user might click the retry function. This is a chance for the app
    to try and fix the underlying issue of the user not present in the CourseUserMap
    table.

    :param course_id: id of the Canvas course
    :return: redirect to the submission page
    """
    user = get_current_user()
    existing_mapping = CourseUserMap.query.filter_by(
        course_id=course_id, user_id=user.id
    ).first()
    if existing_mapping:
        return jsonify({"message": "User is already mapped."}), 400

    try:
        canvas = get_canvas_client(user.canvas_access_token)
        course = canvas.get_course(course_id)
        enrollments = course.get_enrollments(user_id=user.canvas_id)
    except Unauthorized:
        return jsonify({"message": errors.NOT_ENROLLED}), 400

    enrolls = [e.type for e in enrollments]
    role = CourseUserMap.STUDENT
    if "TeacherEnrollment" in enrolls:
        role = CourseUserMap.TEACHER
    elif "TaEnrollment" in enrolls:
        role = CourseUserMap.TA

    new_mapping = CourseUserMap.create(course_id=course_id, user_id=user.id, role=role)
    db.session.add(new_mapping)
    db.session.commit()

    return Response("OK", headers={"Content-Type": "text/plain"})


@api_blueprint.route(
    "/course/<int:course_id>/course-wide-settings/",
    methods=["POST"],
)
@jwt_required
def update_course_settings(course_id):
    """Update the maximum reviews of course

    :param course_id: Canvas ID of the course
    :return: Success message
    """
    data = request.get_json()
    max_reviews = data["max_reviews"] if "max_reviews" in data.keys() else 0
    user = get_current_user()
    try:
        teacher_or_ta = user_is_ta_or_teacher(user, course_id)
    except Unauthorized:
        return jsonify({"message": errors.NOT_ENROLLED}), 400

    canvas = get_canvas_client(user.canvas_access_token)
    course = canvas.get_course(course_id)
    students = course.get_users(enrollment_type=["student"], enrollment_state=["active"])
    student_list_length = len([s.id for s in students])
    
    if int(max_reviews) > student_list_length:
        return jsonify({"message": "There cannot be more reviews per submission than the no.of students enrolled in the course"}), 400

    assignments = course.get_assignments()
    if teacher_or_ta:
        settings = AssignmentSettings.query.filter(
            AssignmentSettings.assignment_id.in_([a.id for a in assignments])
        ).all()

        for setting in settings:
            setting.max_reviews = max_reviews
        db.session.commit()

        return jsonify({"message": "Course Settings Updated"}), 200

    return jsonify({"message": "NOT A TEACHER OR TA"}), 400
