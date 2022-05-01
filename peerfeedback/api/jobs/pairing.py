import itertools
import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from canvasapi.exceptions import InvalidAccessToken, ResourceDoesNotExist
from flask_jwt_extended import get_current_user, jwt_required
from peerfeedback.api import errors
from peerfeedback.api.jobs.sendmail import (
    send_auto_pairing_notification_to_teachers,
    send_pairing_email,
    send_ta_allocation_email,
)
from peerfeedback.api.schemas import pairing_with_task, real_pairing, real_user_schema
from peerfeedback.api.utils import (
    assign_students_to_tas,
    create_pairing,
    create_user,
    generate_non_group_pairs,
    generate_review_matches,
    get_canvas_client,
    get_course_teacher,
    get_db_users,
    validate_csv_input,
)
from peerfeedback.api.views import api_blueprint
from peerfeedback.extensions import db, rq
from peerfeedback.models import AssignmentSettings, Feedback, Pairing, Study, Task, User
from peerfeedback.utils import get_pseudo_names, update_canvas_token
from rq import get_current_job
from sqlalchemy.orm import joinedload

logger = logging.getLogger("rq.worker")


class AutomaticPairing(object):
    def __init__(
        self,
        course_id,
        assignment_id,
        review_rounds,
        user,
        exclude_defaulters,
        excluded_students,
        send_emails,
    ):
        self.course_id = course_id
        self.assignment_id = assignment_id
        self.review_rounds = review_rounds
        self.user = user
        self.exclude_defaulters = exclude_defaulters
        self.excluded_students = [
            s.strip() for s in excluded_students.split(",") if s.strip()
        ]
        logger.debug("Excluding %d students from pairing", len(excluded_students))
        self.send_emails = send_emails

        # Other variables
        self.canvas = None
        self.course = None
        self.assignment = None
        self.assignment_settings = None
        self.all_students = []

    def init_canvas(self, job):
        logger.info("Loading information from Canvas")

        while True:
            try:
                update_canvas_token(self.user)
                self.canvas = get_canvas_client(self.user.canvas_access_token)
                self.course = self.canvas.get_course(self.course_id)
                self.assignment = self.course.get_assignment(self.assignment_id)
                self.assignment_settings = AssignmentSettings.query.filter(
                    AssignmentSettings.assignment_id == self.assignment_id
                ).first()
                self.all_students = self.course.get_users(
                    include=["email"],
                    enrollment_type=["student"],
                    enrollment_state=["active"],
                )
            except InvalidAccessToken:
                continue
            break

        if self.excluded_students:
            self.excluded_students = [
                s.id for s in self.all_students if s.login_id in self.excluded_students
            ]

        job.meta["progress"] = 8
        job.save_meta()

    def pair_for_assignment(self, job):
        """Carry out pairing for a normal assignment based on student submissions

        :param job: Redis queue job to update the progress status
        """
        # Select all the users who have submitted the assignment
        logger.info("Loading student submissions")
        submissions = self.assignment.get_submissions()
        grader_canvas_ids = [
            sub.user_id
            for sub in submissions
            if sub.user_id not in self.excluded_students
        ]
        logger.debug("No. of Graders: %d", len(grader_canvas_ids))
        logger.debug("Graders: %s", grader_canvas_ids)

        submitter_canvas_ids = [
            submission.user_id
            for submission in submissions
            if submission.workflow_state != "unsubmitted"
            and not (
                submission.workflow_state == "graded"
                and submission.score
                and int(submission.score) == 0
            )
            and submission.user_id not in self.excluded_students
        ]
        logger.debug("No.of Submitters: %d", len(submitter_canvas_ids))
        logger.debug("Submitters: %s", submitter_canvas_ids)

        if self.exclude_defaulters:
            logger.debug("Excluding defaulters. Graders are now same as submitters.")
            grader_canvas_ids = submitter_canvas_ids

        # cannot do more rounds than available students
        if self.review_rounds > len(submitter_canvas_ids):
            logger.error(errors.REVIEWS_EXCEED_STUDENTS)
            return {"status": "error", "message": errors.REVIEWS_EXCEED_STUDENTS}

        job.meta["progress"] = 15
        job.save_meta()

        all_users = get_db_users(self.all_students, True)
        usermap = dict((u.id, u) for u in all_users)
        graders = [u.id for u in all_users if u.canvas_id in grader_canvas_ids]
        recipients = [u.id for u in all_users if u.canvas_id in submitter_canvas_ids]

        logger.info("Checking to see if the assignment is a part of a Study")
        studies = Study.query.filter(
            Study.start_date < datetime.now(), Study.end_date > datetime.now()
        ).all()
        pseudo_names = itertools.cycle(get_pseudo_names())

        active_study = None
        study_participants = []
        for study in studies:
            linked_assignments = study.assignments.split(",")
            if str(self.assignment_id) in linked_assignments:
                logger.info("Assignment is a part of Study: %s", study.name)
                active_study = study
                logger.info("Loading study participants")
                study_participants = [p.id for p in active_study.participants]
                logger.info("No. of participants: %d", len(study_participants))
                break

        possible_pairs = len(all_users) * self.review_rounds
        pair_count = 0
        group_map = {}

        if (
            self.assignment.group_category_id
            and not self.assignment.intra_group_peer_reviews
        ):
            # prepare a dictionary of group id with the graders
            group_category = self.canvas.get_group_category(
                self.assignment.group_category_id
            )
            groups = group_category.get_groups()
            for group in groups:
                users = group.get_users()
                group_members = get_db_users(users, False)
                group_map[group.id] = [u.id for u in group_members if u.id in graders]

        logger.info("Generating matches for pairing")
        if group_map:
            _pairs = generate_non_group_pairs(group_map, recipients, self.review_rounds)
            matchings = _pairs.items()
        else:
            matchings = generate_review_matches(graders, recipients, self.review_rounds)

        logger.info("Creating Pairs")
        for grader_id, recipient_ids in matchings:
            logger.debug("Creating pairs for Grader: %d", grader_id)
            grader = usermap[grader_id]
            for recipient_id in recipient_ids:
                recipient = usermap[recipient_id]
                pair_count += 1
                job.meta["progress"] = 30 + int(pair_count / possible_pairs * 70)
                job.save_meta()
                submission = next(
                    (s for s in submissions if s.user_id == recipient.canvas_id), None
                )
                if not submission:
                    continue
                pseudo_name = None
                if (
                    grader_id in study_participants
                    and recipient_id in study_participants
                ):
                    pseudo_name = next(pseudo_names)
                try:
                    pair = create_pairing(
                        self.user,
                        grader,
                        recipient,
                        self.course,
                        self.assignment,
                        study=active_study,
                        pseudo_name=pseudo_name,
                    )
                    if self.send_emails:
                        send_pairing_email.queue(pair.id)
                except (errors.PairingToSelf, errors.PairingExists):
                    logger.warning(
                        "Grader %d and Recipient %d are already paired",
                        grader_id,
                        recipient_id,
                    )

    def pair_for_igr(self, job):
        """Carry out pairing for Intra Group Review assignments. These are single
        blind reviews of group members. More details at:
        https://gitlab.com/gabrieljoel/peerfeedback-ng/-/issues/378

        :params job: Redis queue job to track the progress the of the process
        """
        logger.info("Performing Pairing for Intra Group Review")
        if not self.assignment.group_category_id:
            raise Exception("Assignment is not an group assignment.")

        group_category = self.canvas.get_group_category(
            self.assignment.group_category_id
        )
        groups = group_category.get_groups()

        all_users = get_db_users(self.all_students, True)
        usermap = dict((u.id, u) for u in all_users)
        matchings = []
        total_pairs = 0

        for group in groups:
            users = group.get_users()

            group_members = get_db_users(users, False)

            if len(group_members) == 2:
                continue

            group_ids = [m.id for m in group_members]

            for grader in group_ids:
                matching = (grader, [r for r in group_ids if r != grader])
                matchings.append(matching)
                total_pairs += len(matching[1])

        job.meta["progress"] = 15
        job.save_meta()

        pair_count = 0
        logger.info("Creating Pairings")
        for grader_id, recipients in matchings:
            logger.debug("Creating pairs for Grader: %d", grader_id)
            grader = usermap[grader_id]
            for recipient_id in recipients:
                recipient = usermap[recipient_id]
                pair_count += 1
                job.meta["progress"] = 30 + int(pair_count / total_pairs * 70)
                job.save_meta()
                try:
                    pair = create_pairing(
                        self.user,
                        grader,
                        recipient,
                        self.course,
                        self.assignment,
                        pair_type=Pairing.IGR,
                    )
                    if self.send_emails:
                        send_pairing_email.queue(pair.id)
                except (errors.PairingToSelf, errors.PairingExists):
                    logger.warning(
                        "Grader %d and Recipient are already paired",
                        grader_id,
                        recipient_id,
                    )

    def process(self, job):
        self.init_canvas(job)
        if self.assignment_settings.intra_group_review:
            self.pair_for_igr(job)
        else:
            self.pair_for_assignment(job)

        if self.send_emails:
            logger.info("Sending pairing completed notification to teachers")
            send_auto_pairing_notification_to_teachers.queue(
                self.course_id, self.assignment_id
            )
        return "Automatic Pairing completed successfully"


@rq.job("high", timeout=60 * 60)
def pair_automatically(
    course_id,
    assignment_id,
    review_rounds,
    user_id,
    exclude_defaulters,
    excluded_students,
    send_emails,
):
    """RedisQueue job that does automatic pairing

    :param course_id: Canvas course id
    :param assignment_id: Canvas assignment id
    :param review_rounds: No.of reviews assigned per student
    :param user_id: the user who is initiating the pairing operation
    :param exclude_defaulters: should the students who didn't submit be excluded
        from the pairing process
    :param excluded_students: comma-seperated string of usernames who shouldn't
        be a part of the pairing process
    :param send_emails: should the emails be sent
    """
    logger.info(
        "Automatic Pairing started with params (%d, %d, %d, %d, %s, '%s', %s)",
        course_id,
        assignment_id,
        review_rounds,
        user_id,
        exclude_defaulters,
        excluded_students,
        send_emails,
    )

    user = User.query.get(user_id)
    job = get_current_job()
    if not user:
        logger.error("Pairing Stopped: " + errors.INVALID_USER_ID)
        return {"status": "error", "message": errors.INVALID_USER_ID}

    processor = AutomaticPairing(
        course_id,
        assignment_id,
        review_rounds,
        user,
        exclude_defaulters,
        excluded_students,
        send_emails,
    )
    try:
        message = processor.process(job)
    except Exception as e:
        logger.exception(e)
        return {
            "status": "error",
            "message": f"{e}\n\nFailed to complete pairing. Contact Administrator.",
        }

    logger.info(message)
    return {"status": "success", "message": message}


@rq.job("high", timeout=60 * 15)
def pair_using_csv(
    course_id,
    assignment_id,
    pairs,
    allow_missing,
    grader_type,
    user_id,
    send_emails,
    run_as_job=True,
):
    """Performs pairing based on a mapping extracted from the CSV input in the
    frontend.

    :param course_id: Canvas course ID
    :param assignment_id: Canvas Assignment ID
    :param pairs: the mapping of graders and the recipients
    :param allow_missing: Allow students who have not submitted their assignment
        to be paired as well
    :param grader_type: "STUDENT" or "TA"
    :param user_id: the user initiating this job. Should be registered as the
        teacher or TA for the course
    :param send_emails: bool - should the intimation emails be sent to the
        students about the pairing
    :param run_as_job: bool - set to false when the job is executed from the
        flask shell as a function
    ":return: the status of the job as a dict(status,message)
    """
    user = User.query.get(user_id)
    if not user:
        return {"status": "error", "message": errors.INVALID_USER_ID}

    if run_as_job:
        job = get_current_job()
        job.meta["progress"] = 5
        job.save_meta()

    token_expiry = datetime.now(tz=timezone.utc) + timedelta(minutes=15)
    if token_expiry > user.canvas_expiration_time:
        update_canvas_token(user)

    validation = validate_csv_input(course_id, pairs, grader_type)

    if validation["status"] == "error":
        return validation

    course_ids = validation["course_ids"]
    course_usernames = validation["course_usernames"]
    students = validation["students"]
    course = validation["course"]
    assignment = course.get_assignment(assignment_id)

    if run_as_job:
        job.meta["progress"] = 20
        job.save_meta()

    # Ensure all the users are present
    users = User.query.filter(User.canvas_id.in_(course_ids)).all()
    user_map = {user.username: user for user in users}
    existing_canvas_ids = [user.canvas_id for user in users]

    if len(existing_canvas_ids) != len(course_usernames):
        new_users = [
            create_user(student)
            for student in students
            if student.id not in existing_canvas_ids
        ]
        db.session.add_all(new_users)
        db.session.commit()
        user_map.update({user.username: user for user in new_users})

    if run_as_job:
        job.meta["progress"] = 30
        job.save_meta()

    submissions = assignment.get_submissions()
    missing_submissions = []
    total_pairs = len(pairs)
    paired = 0

    for pair in pairs:
        grader = user_map[pair["grader"]]
        for r_username in pair["recipients"]:
            recipient = user_map[r_username]
            submission = next(
                (s for s in submissions if s.user_id == recipient.canvas_id), None
            )
            # Conditions under which we consider submission is missing
            submission_is_missing = (
                submission is None
                or submission.workflow_state == "unsubmitted"
                or (
                    submission.workflow_state == "graded" and int(submission.score) == 0
                )
            )
            if submission_is_missing and not allow_missing:
                missing_submissions.append(r_username)
                continue
            try:
                pair = create_pairing(user, grader, recipient, course, assignment)
                if send_emails:
                    send_pairing_email.queue(pair.id)
            except (errors.PairingExists, errors.PairingToSelf):
                continue

        paired += 1
        if run_as_job:
            job.meta["progress"] = 30 + paired / total_pairs * 70

    if missing_submissions:
        message = "Pairing was done. Some were skipped due to missing submissions: "
        message += ",".join(missing_submissions)
        return {"status": "success", "message": message}
    return {"status": "success", "message": "Students were paired successfully."}


@rq.job("high")
def allocate_students_to_tas(
    course_id, assignment_id, user_id, allocations, send_email
):
    """Allocates certain number of student assignments to be reviewed by each
    TA as mentioned in the allocations

    :param course_id: Canvas ID of the course
    :param assignment_id: Canvas ID of the assignment
    :param user_id: local id of the user in the database
    :param allocations: list of dicts containing the TA id and student count
                        [{"ta_id": <int>, "student_count": <int>}, ...]
    :param send_email: boolen flag indicating if emails need to be sent or not
    :return: dict with "status" and "message"
    """
    job = get_current_job()

    # validate the json format before making any costly network calls
    properly_formatted = all(
        ["ta_id" in x and "student_count" in x for x in allocations]
    )
    if not properly_formatted:
        return {"status": "error", "message": errors.INVALID_DATA_FORMAT}

    user = User.query.get(user_id)
    if not user:
        return {"status": "error", "message": errors.INVALID_USER_ID}

    # check for previous allocations and jump to the other function
    existing = Pairing.query.filter(
        Pairing.course_id == course_id,
        Pairing.assignment_id == assignment_id,
        Pairing.type == Pairing.TA,
    ).all()

    if len(existing):
        return reassign_ta_pairings(
            job, course_id, assignment_id, user, allocations, send_email
        )

    canvas = get_canvas_client(user.canvas_access_token)
    course = canvas.get_course(course_id)
    assignment = course.get_assignment(assignment_id)
    students = course.get_users(enrollment_type=["student"])
    job.meta["progress"] = 5
    job.save_meta()
    student_users = get_db_users(students, create_missing=True)
    student_users = sorted(student_users, key=lambda x: x.id)
    job.meta["progress"] = 10
    job.save_meta()

    tas = [a["ta_id"] for a in allocations]
    ta_users = User.query.filter(User.id.in_(tas)).all()
    student_ids = [a.id for a in student_users]

    allotted = assign_students_to_tas(allocations, student_ids)
    job.meta["progress"] = 15
    job.save_meta()

    possible_pairs = len(student_ids)
    pairs_created = 0

    for ta in allotted:
        grader_id = int(ta["ta_id"])
        grader = next((u for u in ta_users if u.id == grader_id), 0)
        for stu in ta["student_ids"]:
            recipient = student_users[student_ids.index(stu)]
            pairs_created += 1
            job.meta["progress"] = 15 + int(pairs_created / possible_pairs * 85)
            job.save_meta()
            try:
                create_pairing(user, grader, recipient, course, assignment, Pairing.TA)
            except (errors.PairingToSelf, errors.PairingExists):
                continue
        if send_email:
            send_ta_allocation_email.queue(course_id, assignment_id, grader_id)

    return {"status": "success", "message": "Students have been allocated to the TAs"}


def reassign_ta_pairings(job, course_id, assignment_id, user, allocations, send_email):
    """Function that reassigns the students to the TAs

    :param job: the original job that calls the function
    :param course_id: canvas id of the course
    :param assignment_id: canvas id of the assignment
    :param user: user making the request
    :param allocations: the ta id and student count mapping
    :param send_email: bool indicating if emails need to be sent to the graders
    :return:
    """
    allotment = {a["ta_id"]: a["student_count"] for a in allocations}
    existing_pairs = Pairing.query.filter(
        Pairing.course_id == course_id,
        Pairing.assignment_id == assignment_id,
        Pairing.grader_id.in_(allotment.keys()),
    ).all()
    existing = {ta: 0 for ta in allotment.keys()}
    for pair in existing_pairs:
        existing[pair.grader_id] += 1

    extras = {}
    shortage = {}
    for ta, existing_count in existing.items():
        difference = existing_count - allotment.get(ta, 0)
        if difference > 0:
            extras[ta] = difference
        elif difference < 0:
            shortage[ta] = abs(difference)

    job.meta["progress"] = 15
    job.save_meta()

    try:
        assert sum(extras.values()) == sum(shortage.values())
    except AssertionError:
        return {
            "status": "error",
            "message": "There is a mismatch in the number of pairs being reasssigned.",
        }

    extra_pairs = []
    for ta, extra in extras.items():
        pending_fbs = (
            Feedback.query.filter(
                Feedback.course_id == course_id,
                Feedback.assignment_id == assignment_id,
                Feedback.reviewer_id == ta,
                Feedback.draft.is_(True),
            )
            .options(joinedload(Feedback.pairing))
            .all()
        )
        pairs = [fb.pairing for fb in pending_fbs[0:extra]]
        extra_pairs.extend(pairs)

    unallocated_students = []
    for pair in extra_pairs:
        unallocated_students.append(pair.recipient_id)
        pair.delete()

    job.meta["progress"] = 50
    job.save_meta()

    canvas = get_canvas_client(user.canvas_access_token)
    course = canvas.get_course(course_id)
    assignment = course.get_assignment(assignment_id)
    start = 0
    total_tas = len(shortage)
    ta_count = 1
    for ta, required in shortage.items():
        student_ids = unallocated_students[start : start + required]
        ta_user = User.query.get(ta)
        for sid in student_ids:
            student = User.query.get(sid)
            try:
                create_pairing(user, ta_user, student, course, assignment, Pairing.TA)
            except (errors.PairingToSelf, errors.PairingExists):
                continue

        if send_email:
            send_ta_allocation_email.queue(course_id, assignment_id, ta)
        job.meta["progress"] = 50 + (ta_count / total_tas * 50)
        job.save_meta()

    job.meta["progress"] = 100
    job.save_meta()
    return {"status": "success", "message": "Re-allotment of TA tasks is complete."}


@rq.job("high", timeout=60 * 15)
def replace_task_and_generate_new_pairing(task_id, send_emails):
    """Archives the given task and creates a new pairing and task for the user.
    This is usually when the task assigned to the user becomes invalid due to
    the submission going missing after the pairing is complete.

    :param task_id: id of the task to be replaced
    :param send_emails: boolean flag indicate if emails should be sent
    :return: new task as a JSON
    """
    task = Task.query.get(task_id)
    if not task:
        return None
    job = get_current_job()
    task.status = Task.ARCHIVED
    task.save()

    job.meta["progress"] = 20
    job.save_meta()

    grader = creator = task.user
    teacher = get_course_teacher(task.course_id)
    canvas = get_canvas_client(teacher.canvas_access_token)
    course = canvas.get_course(task.course_id)
    assignment = course.get_assignment(task.assignment_id)

    # pick the user with a valid submission who is receiving the least amount
    # of reviews
    sql = f"""SELECT recipient_id, count(recipient_id) FROM pairing
    WHERE assignment_id={task.assignment_id} AND recipient_id NOT IN (
        SELECT recipient_id FROM pairing
        WHERE assignment_id={task.assignment_id} AND grader_id={task.user_id}
    )
    GROUP BY recipient_id;"""
    query_result = db.session.execute(sql).fetchall()
    recipients = sorted(query_result, key=lambda x: x[1])
    submission = None
    recipient = None

    for recipient_id, count in recipients:
        recipient = User.query.get(recipient_id)
        try:
            submission = assignment.get_submission(recipient.canvas_id)
        except ResourceDoesNotExist:
            continue
        # Ensure the submission is not empty
        if submission.workflow_state != "unsubmitted" and not (
            submission.workflow_state == "graded" and int(submission.score) == 0
        ):
            break

    job.meta["progress"] = 50
    job.save_meta()

    if not submission:
        return {"status": "error", "message": "No submissions found"}
    if not recipient:
        return {"status": "error", "message": "No suitable students found for pairing"}

    pair = create_pairing(creator, grader, recipient, course, assignment)
    if send_emails:
        send_pairing_email.queue(pair.id)

    job.meta["progress"] = 100
    job.save_meta()
    return {
        "status": "success",
        "message": "Task replaced and new pairing created.",
        "recipient_id": pair.recipient_id,
    }


@api_blueprint.route("/course/<int:course_id>/assignment/<int:assignment_id>/groups/")
@jwt_required
def get_all_groups(course_id, assignment_id):
    """Get the feedback submitted for a particular user's submission

    :param course_id: canvas id of the course
    :param assignment_id: canvas id of the assignment
    :return: list of feedback as JSON
    """
    user = get_current_user()
    canvas = get_canvas_client(user.canvas_access_token)
    course = canvas.get_course(course_id)
    assignment = course.get_assignment(assignment_id)
    group_map = {}
    pair_query = Pairing.query.filter(
        Pairing.course_id == course_id,
        Pairing.assignment_id == assignment_id,
        Pairing.archived.is_(False),
    ).options(joinedload(Pairing.task))

    if assignment.group_category_id and not assignment.intra_group_peer_reviews:
        # prepare a dictionary of group id with the graders
        group_category = canvas.get_group_category(assignment.group_category_id)
        groups = group_category.get_groups()
        for group in groups:
            users = group.get_users()
            group_members = get_db_users(users, False)
            grader_ids = [u.id for u in group_members]
            pairs = pair_query.filter(Pairing.grader_id.in_(grader_ids)).all()
            pair_table = defaultdict(list)
            for p in pairs:
                pair_table[p.grader.id].append(p)
            pairs = [
                dict(
                    id=g,
                    pairing=real_pairing.dump(pair_table[g], many=True),
                )
                for g in grader_ids
                if pair_table[g]
            ]
            group_map[group.id] = pairs

        return group_map

    return {}
