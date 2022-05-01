import csv
import datetime
import io
import logging
import os
import statistics

from dateutil.parser import parse as parse_date
from peerfeedback.api.jobs.sendmail import (
    send_download_email,
    send_export_request_received_email,
)
from peerfeedback.api.utils import (
    get_canvas_client,
    get_db_users,
    make_csv,
    upload_file_to_s3,
)
from peerfeedback.crons import award_ml_grade
from peerfeedback.extensions import db, rq
from peerfeedback.models import (
    AssignmentSettings,
    CourseUserMap,
    Feedback,
    Pairing,
    RubricCriteria,
    User,
)
from sqlalchemy import text
from sqlalchemy.orm import joinedload

logger = logging.getLogger(__name__)


@rq.job("high", timeout=60 * 10)
def export_course_data(course_id, user_id, include_drafts, run_ai, assignment_id=None):
    """Generates data report of the course and send email to the user when ready

    :param course_id: ID of the Course
    :param user_id: User's ID
    :param include_drafts: Boolean flag to include drafts in the export or not
    :param run_ai: Boolean flag indicating if the ML Scores should be generated
        before the export is prepared
    :param assignment_id: OPTIONAL - the ID of the assignment to filter the data.
        By default the data for all the assignments are exported. This can be
        limited to a specific assignment by setting the assignment.
            By default the data for all the assignments are exported. This can be
            limited to a specific assignment by setting the assignment ID
    """
    user = User.query.get(user_id)
    if not user:
        return

    # Send an email to the user before starting the processing
    send_export_request_received_email(user, course_id)

    canvas = get_canvas_client(user.canvas_access_token)
    course = canvas.get_course(course_id)
    assignments = course.get_assignments()
    assignment_map = {a.id: f"{a.name} ({a.id})" for a in assignments}
    group_maps = {a.id: generate_user_group_map(canvas, course, a) for a in assignments}

    if run_ai:
        # set the num as None so there is not limiting value and all feedback
        # get processed
        award_ml_grade(num=None, course_id=course_id)

    GRADER_ID_INDEX = 17
    DRAFT_INDEX = 16
    RUBRIC_ID_INDEX = 15
    GRADES_INDEX = 6
    ASSIGNMENT_ID_INDEX = 0

    feedback_sql = """
    SELECT
        feedback.assignment_id,
        RECIPIENT.canvas_id,
        RECIPIENT.name,
        GRADER.username,
        RECIPIENT.username,
        feedback.value,
        feedback.grades,
        feedback.start_date,
        feedback.end_date,
        feedback.read_time,
        feedback.write_time,
        feedback.ml_rating,
        feedback.ml_prob,
        meta_feedback.points,
        meta_feedback.comment,
        feedback.rubric_id,
        NOT feedback.draft,
        GRADER.id,
        'feedback'
    FROM feedback
    LEFT JOIN
        users AS GRADER ON GRADER.id = feedback.reviewer_id
    LEFT JOIN
        users AS RECIPIENT ON RECIPIENT.id = feedback.receiver_id
    LEFT JOIN
        meta_feedback ON feedback.id = meta_feedback.feedback_id
    """

    if assignment_id:
        where_clause = f"""
    WHERE feedback.assignment_id='{assignment_id}'
    """
    else:
        where_clause = f"""
    WHERE feedback.assignment_id IN (
        SELECT assignment_id FROM assignment_settings WHERE course_id='{course_id}'
    )"""

    feedback_sql = feedback_sql + where_clause
    if include_drafts:
        feedback_sql = text(feedback_sql + ";")
    else:
        feedback_sql = text(feedback_sql + " AND feedback.draft=false;")

    comments_sql = text(
        f"""
    SELECT
        comment.assignment_id,
        recipient.canvas_id,
        recipient.name,
        grader.username,
        recipient.username,
        comment.value,
        'na',
        'na',
        comment.created_on AT TIME ZONE 'UTC',
        'na',
        'na',
        'na',
        'na',
        'na',
        comment.assignment_id,
        'na',
        'na',
        'na',
        'comment'
        FROM comment
        LEFT JOIN
            users AS grader ON grader.id = comment.commenter_id
        LEFT JOIN
            users AS recipient ON recipient.id = comment.recipient_id
        WHERE course_id='{course_id}';
    """
    )

    result = db.engine.execute(feedback_sql)
    feedback_rows = [list(row) for row in result.fetchall()]
    for row in feedback_rows:
        assignment_id = row[ASSIGNMENT_ID_INDEX]
        user_group_map = group_maps[assignment_id]
        grader_id = row[GRADER_ID_INDEX]
        row[GRADER_ID_INDEX] = user_group_map.get(grader_id, 0)

        row[ASSIGNMENT_ID_INDEX] = assignment_map[assignment_id]

    prev_rubric_id = -1
    rubric_criteria = []
    for f in feedback_rows:
        rubric_id = f[RUBRIC_ID_INDEX]

        if rubric_id:
            if rubric_id != prev_rubric_id:
                rubric_criteria = (
                    RubricCriteria.query.filter(rubric_id == rubric_id)
                    .order_by(RubricCriteria.id)
                    .all()
                )

            grades = f[GRADES_INDEX]
            grade_calc = 0

            submitted = f[DRAFT_INDEX]

            if submitted:
                for i, grade in enumerate(grades):
                    try:
                        criteria_id = grade["criteria_id"]
                        criteria = next(
                            filter(lambda x: x.id == criteria_id, rubric_criteria)
                        )
                        cur_criteria = criteria.levels
                    except KeyError:
                        rubric_levels = [rc.levels for rc in rubric_criteria]
                        cur_criteria = rubric_levels[i]

                    level = grade["level"]

                    if level == None:
                        f.append("No level selected")
                    else:
                        cur_level = next(
                            filter(lambda x: x["position"] == level, cur_criteria)
                        )
                        grade_calc = grade_calc + cur_level["points"]
                        f.append(cur_level["points"])

            f[GRADES_INDEX] = grade_calc
        else:
            f[GRADES_INDEX] = "no rubric"

        prev_rubric_id = rubric_id

    result = db.engine.execute(comments_sql)
    comment_rows = [list(row) for row in result.fetchall()]
    for row in comment_rows:
        row[0] = assignment_map[row[0]]
        row.append("")

    heading = [
        "Assignment",
        "ID",
        "Student",
        "grader username",
        "recipient username",
        "feedback comment",
        "feedback score",
        "feedback start date",
        "feedback end date",
        "feedback read time",
        "feedback write time",
        "automated feedback comment evaluation (0 = thumbs down, 1 = neutral, 2 = thumbs up)",
        "automated feedback probability (how confident is the robot of its judgement)",
        "meta feedback score",
        "meta feedback comment",
        "rubric id",
        "submitted",
        "group id",
        "feedback or comment",
        "Section",
    ]

    for rc in rubric_criteria:
        heading.append(rc.name + " " + rc.description)

    csv_data = make_csv(feedback_rows + comment_rows, heading)
    today = datetime.date.today()

    if os.getenv("ENV", "prod") == "dev":
        print("")
        print(csv_data.getvalue())
        print("")
        return

    if assignment_id == None:
        file_url = upload_file_to_s3(
            csv_data, f"{course_id}_{assignment_id}_{today}_assign_detailed_data.csv"
        )
        send_download_email(user, file_url, course_id, assignment_id)
    else:
        file_url = upload_file_to_s3(
            csv_data, str(course_id) + "_" + str(today) + "_course_data_export.csv"
        )
        send_download_email(user, file_url, course_id)


def generate_user_group_map(canvas, course, assignment):
    """Generate a map of all the students and their group ids for the given
    assignment.
    """
    logger.info("Mapping students to their groups")
    course_students = (
        CourseUserMap.query.filter(
            CourseUserMap.course_id == course.id,
            CourseUserMap.role == CourseUserMap.STUDENT,
        )
        .options(joinedload(CourseUserMap.user))
        .all()
    )

    if not assignment.group_category_id:
        return {s.user_id: 0 for s in course_students}

    group_category = canvas.get_group_category(assignment.group_category_id)
    groups = group_category.get_groups()
    canvas_map = {c.user.canvas_id: c.user for c in course_students}
    user_group_map = {}
    for group in groups:
        logger.debug("Processing group: %d - %s", group.id, group.name)
        members = group.get_users()
        for member in members:
            if member.id not in canvas_map:
                continue
            user = canvas_map[member.id]
            user_group_map[user.id] = group.id
    return user_group_map


@rq.job("high", timeout=60 * 10)
def export_assignment_data(course_id, assignment_id, user_id):
    """Generate the data export for the given assignment and sends an email to
    the user when the file is ready for download.

    :param course_id: Course ID
    :param assignment_id: Assignment ID
    :param user_id: Id if the user who requested the download
    """
    user = User.query.get(user_id)
    send_export_request_received_email(user, course_id, assignment_id)

    settings = AssignmentSettings.query.filter_by(assignment_id=assignment_id).first()

    canvas = get_canvas_client(user.canvas_access_token)
    course = canvas.get_course(course_id)
    assignment = course.get_assignment(assignment_id)
    submission_deadline = assignment.due_at

    if settings.deadline_format == "canvas":
        deadline = parse_date(submission_deadline, ignoretz=True) + datetime.timedelta(
            days=settings.feedback_deadline
        )
    else:
        deadline = settings.custom_deadline

    user_group_map = {}
    if settings.intra_group_review:

        user_group_map = generate_user_group_map(canvas, course, assignment)

    query = (
        Feedback.query.filter(
            Feedback.assignment_id == assignment_id,
            Feedback.draft.is_(False),
            Feedback.pairing.has(Pairing.archived.is_(False)),
        )
        .order_by(Feedback.reviewer_id, Feedback.end_date.desc())
        .options(joinedload(Feedback.reviewer))
        .all()
    )

    scores = []

    FB_SCORE_POSITION = 7
    TOTAL_SCORE_POSITION = 8

    for review in query:

        if not settings.intra_group_review and not review.end_date:
            continue

        points = 0
        if not settings.intra_group_review:
            delta = deadline - review.end_date
            decimal_d = delta / datetime.timedelta(days=1)
            days = int(decimal_d)
            if days < 0:
                points = 50 - (abs(days) * 10)
                if points < 0:
                    points = 0
            else:
                points = 50

        review_score = []
        review_score.append(review.reviewer.id)
        review_score.append(review.reviewer.name)
        review_score.append(review.reviewer.username)
        review_score.append(user_group_map.get(review.reviewer.id, 0))
        review_score.append(review.value)
        review_score.append(review.end_date)
        review_score.append(deadline)
        review_score.append(points)
        review_score.append(0)
        review_score.append(review.draft)
        review_score.append(review.ml_rating)
        review_score.append(review.ml_prob)

        scores.append(review_score)

    first_reviewer_id = scores[0][0]
    current_reviewer_id = first_reviewer_id
    current_scores = []
    scores.append([-1])
    for score in scores:
        if current_reviewer_id != score[0] or score[0] == -1:
            total_score = 0
            current_scores.sort(reverse=True)
            for index, c in zip(range(2), current_scores):
                total_score = c[FB_SCORE_POSITION] + total_score

            for c in current_scores:
                c[TOTAL_SCORE_POSITION] = total_score

            current_reviewer_id = score[0]
            current_scores = []

        current_scores.append(score)

    scores.pop()

    heading = [
        "reviewer_id",
        "name",
        "username",
        "group_id (if applicable)",
        "feedback",
        "end date",
        "deadline",
        "feedback score",
        "total score",
        "draft",
        "ml rating",
        "ml prob",
    ]

    csv_data = make_csv(scores, heading)
    today = datetime.date.today()
    file_url = upload_file_to_s3(
        csv_data, str(assignment_id) + "_" + str(today) + "_assignment_data_export.csv"
    )

    send_download_email(user, file_url, course_id)


@rq.job("high", timeout=60 * 10)
def export_student_scores(course_id, assignment_id, user_id):
    """Exports the scores from the feedback received by each student. The
    generated CSV file has 5 fields
    1. User Name
    2. Assignment ID
    3. No.of feedback the student received
    4. The Average score
    5. Standard Deviation

    :param course_id: ID of the course
    :param assignment_id: ID of the assignment whose scores are to be generated
    :param user_id: ID of the user requesting the export
    """
    # Get the assignment rubric and the criteria
    settings = AssignmentSettings.query.filter(
        AssignmentSettings.assignment_id == assignment_id
    ).first()

    user = User.query.get(user_id)
    canvas = get_canvas_client(user.canvas_access_token)
    course = canvas.get_course(course_id)
    assignment = course.get_assignment(assignment_id)

    criterias = RubricCriteria.query.filter(
        RubricCriteria.rubric_id == settings.rubric_id
    ).all()
    lookup_table = [
        {l["position"]: l["points"] for l in criteria.levels} for criteria in criterias
    ]

    # Get all the users of the course
    mappings = (
        CourseUserMap.query.filter(
            CourseUserMap.course_id == course_id,
            CourseUserMap.role == CourseUserMap.STUDENT,
        )
        .options(joinedload(CourseUserMap.user))
        .all()
    )

    si = io.StringIO()
    cw = csv.writer(si)
    heading = [
        "Student",
        "ID",
        "Section",
        "Reviews",
        f"{assignment.name} ({assignment_id})",
        "Std Dev",
    ]
    cw.writerow(heading)

    # For each user get all the feedback where he is the recipient
    rows = []
    for mapping in mappings:
        student = mapping.user
        fbs = Feedback.query.filter(
            Feedback.assignment_id == assignment_id,
            Feedback.receiver_id == student.id,
            Feedback.draft.is_(False),
            Feedback.pairing.has(Pairing.archived.is_(False)),
        ).all()
        scores = []
        for fb in fbs:
            total = sum(
                lookup[grade["level"]] for lookup, grade in zip(lookup_table, fb.grades)
            )
            scores.append(total)

        # Calculate the average & std.dev of all the feedback ratings
        count = len(scores)
        avg = statistics.mean(scores) if count > 0 else 0
        stdv = statistics.stdev(scores) if count > 1 else 0
        rows.append([student.name, student.canvas_id, "", count, avg, stdv])
    rows = sorted(rows, key=lambda row: row[-1])
    cw.writerows(rows)

    if os.getenv("ENV", "prod") == "dev":
        print("\n")
        print(si.getvalue())
        print("\n")
        return

    today = datetime.date.today()
    file_url = upload_file_to_s3(
        si, f"assignment_{assignment_id}_student_scores_{today}.csv"
    )
    user = User.query.get(user_id)
    send_download_email(user, file_url, course_id, assignment_id)


@rq.job("high", timeout=60 * 10)
def export_igr_data(course_id, assignment_id, user_id):
    """Exports the data for the Intra-Group Review and mails it to the user.

    :param course_id: Canvas Course ID
    :param assignment_id: Canvas Assignment ID
    :param user_id: ID of the user who requested the download CSV
    """
    logger.info("Starting to prepare data export for IGR: %d", assignment_id)
    user = User.query.get(user_id)
    logger.info("Sending 'request received' email notification")
    send_export_request_received_email(user, course_id, assignment_id)

    settings = AssignmentSettings.query.filter(
        AssignmentSettings.assignment_id == assignment_id
    ).first()
    crits = RubricCriteria.query.filter(
        RubricCriteria.rubric_id == settings.rubric_id
    ).all()
    criteria = {}
    column_names = [
        "Assignment",
        "Project Group",
        "Student Name",
        "GT ID",
        "Recipient GT ID",
    ]

    group_map = {}

    canvas = get_canvas_client(user.canvas_access_token)
    course = canvas.get_course(course_id)
    assignment = course.get_assignment(assignment_id)
    group_category = canvas.get_group_category(assignment.group_category_id)
    groups = group_category.get_groups()

    for group in groups:
        users = group.get_users()
        group_members = get_db_users(users, False)
        group_map.update({m.id: group.id for m in group_members})

    for c in crits:
        points = [i["points"] for i in c.levels]
        criteria[c.id] = {"name": c.name, "points": points}
        column_names.append(c.name)

    column_names += ["Feedback", "Total Points"]

    fbs = (
        Feedback.query.filter(
            Feedback.assignment_id == assignment_id,
            Feedback.draft.is_(False),
            Feedback.pairing.has(Pairing.archived.is_(False)),
        )
        .order_by(Feedback.reviewer_id, Feedback.receiver_id)
        .options(joinedload(Feedback.reviewer), joinedload(Feedback.receiver))
        .all()
    )

    rows = []
    for fb in fbs:
        try:
            row = [
                assignment_id,
                group_map[fb.reviewer_id],
                fb.reviewer.name,
                fb.reviewer.username,
                fb.receiver.username,
            ]
        except KeyError:
            row = [
                assignment_id,
                0,
                fb.reviewer.name,
                fb.reviewer.username,
                fb.receiver.username,
            ]

        points = []

        if len(fb.grades) == 0:
            continue

        for g in fb.grades:
            level = 0
            if g["level"]:
                level = g["level"]

            points.append(criteria[g["criteria_id"]]["points"][level])

        assert len(crits) == len(points)
        row += points
        row.append(fb.value)
        row.append(sum(points))
        rows.append(row)

    csv_data = make_csv(rows, column_names)
    today = datetime.date.today()
    logger.info("Uploading output file to S3 Bucket")
    file_url = upload_file_to_s3(
        csv_data, str(assignment_id) + "_" + str(today) + "_intra_group_review_data.csv"
    )

    logger.info("Sending download email")
    send_download_email(user, file_url, course_id)
    logger.info("Data Export for IGR %d completed.", user_id)
