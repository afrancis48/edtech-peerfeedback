from rq import get_current_job

from peerfeedback.api import errors
from peerfeedback.api.utils import get_canvas_client, create_user
from peerfeedback.extensions import rq
from peerfeedback.models import User, AssignmentSettings, CourseUserMap


@rq.job("high")
def import_course_information(course_id, user_id, run_as_job=True):
    """The job that fetches all the users of the given course and creates a map
    of the users and their roles in the course. This should be started by the
    professor, because only professors have the access for all the users data.

    :param course_id: Canvas course's ID
    :param user_id: local user id
    :param run_as_job: flag indicating if it is run as a job from app or from
        the command line as a function
    :return: status as a dict
    """

    if run_as_job:
        job = get_current_job()
        job.meta["progress"] = 1
        job.meta["message"] = "Initializing course {0}".format(course_id)
        job.save_meta()

    user = User.query.get(user_id)
    canvas = get_canvas_client(user.canvas_access_token)
    course = canvas.get_course(course_id)
    enrollments = course.get_enrollments(user_id=user.canvas_id)
    enrolls = [e.type for e in enrollments]
    if "TeacherEnrollment" not in enrolls:
        if run_as_job:
            job.meta["message"] = errors.ONLY_TEACHERS
            job.save_meta()
        return {"status": "fail", "message": errors.ONLY_TEACHERS}

    if run_as_job:
        job.meta["message"] = "Setting up the course assignments."
        job.meta["progress"] = 5
        job.save_meta()

    assignments = course.get_assignments()
    for assignment in assignments:
        existing = AssignmentSettings.query.filter_by(
            assignment_id=assignment.id
        ).first()
        if existing:
            continue
        settings = AssignmentSettings.create(
            course_id=course.id,
            assignment_id=assignment.id,
            allow_student_pairing=False,
            allow_view_peer_assignments=False,
            feedback_suggestion="",
            max_reviews=0,
            use_rubric=False,
            feedback_deadline=7,
        )
        settings.save()

    if run_as_job:
        job.meta["progress"] = 30
        job.meta["message"] = "Importing users in the course"
        job.save_meta()

    course_users = course.get_users(include=["enrollments"])
    for cu in course_users:
        try:
            user = create_user(cu)
        except:
            continue
        mapping = CourseUserMap.query.filter_by(
            course_id=course_id, user_id=user.id
        ).first()
        if mapping:
            mapping.role = CourseUserMap.role_of(cu.enrollments[0]["type"])
        else:
            mapping = CourseUserMap.create(
                course_id=course_id,
                user_id=user.id,
                role=CourseUserMap.role_of(cu.enrollments[0]["type"]),
            )
        mapping.save()

        if run_as_job and job.meta["progress"] < 90:
            job.meta["progress"] += 1
            job.save_meta()

    if run_as_job:
        job.meta["progress"] = 100
        job.meta["message"] = "Course initialization completed successfully."
        job.save_meta()

    return {
        "status": "success",
        "message": "Course {0} has been initialized.".format(course.name),
    }
