from random import choice

from peerfeedback.api import errors
from peerfeedback.api.jobs.sendmail import send_pairing_email
from peerfeedback.api.utils import (create_pairing, get_canvas_client,
                                    get_course_teacher, proper_email)
from peerfeedback.extensions import db, rq
from peerfeedback.models import Feedback, Pairing, User
from sqlalchemy import Text
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.attributes import flag_modified


@rq.job("low")
def cleanup_grades():
    feedbacks = Feedback.query.filter(Feedback.grades.cast(Text).contains("name")).all()
    fixed = []
    for feedback in feedbacks:
        print("Processing feedback: {0}".format(feedback.id))
        new_grades = []
        for grade in feedback.grades:
            if "name" in grade:
                grade["criteria"] = grade.pop("name")
                fixed.append(feedback.id)
            new_grades.append(grade)
        feedback.grades = new_grades
        flag_modified(feedback, "grades")
        feedback.save()
    print("{0} feedback grades fixed.".format(len(set(fixed))))


@rq.job("low")
def replace_unsubmitted_pairs(course_id, assignment_id, pairs):
    """A background job that will get the remove the pairings whose recipients
    have not submitted the feedback. Then new pairings would be created until
    every student who has submitted the assignment has tasks equal to the no of
    pairs specified in the pairs argument

    :param course_id: id of the canvas course
    :param assignment_id: id of the course's assignment
    :param pairs: the no.of pairs that should be created for every student who
        has submitted the assignment
    :return: None
    """
    teacher = get_course_teacher(course_id)
    if not teacher:
        print("Couldn't find the teacher user for course: {0}".format(course_id))
        return

    canvas = get_canvas_client(teacher.canvas_access_token)
    course = canvas.get_course(course_id)
    assignment = course.get_assignment(assignment_id)
    submissions = assignment.get_submissions()
    unsubmitted = []
    submitted = []
    for s in submissions:
        if s.workflow_state == "unsubmitted":
            unsubmitted.append(s)
        else:
            submitted.append(s)

    unsubmitted_users = [u.user_id for u in unsubmitted]

    pairings = (
        Pairing.query.filter(
            Pairing.course_id == course_id, Pairing.assignment_id == assignment_id
        )
        .options(joinedload(Pairing.recipient))
        .all()
    )
    empty_pairs = list(
        filter(lambda p: p.recipient.canvas_id in unsubmitted_users, pairings)
    )

    for pair in empty_pairs:
        pair.delete(False)  # False = don't commit session after every delete
    db.session.commit()
    print("Deleted {0} pairs with empty submissions.".format(len(empty_pairs)))

    valid_pairs = [
        p for p in pairings if p.recipient.canvas_id not in unsubmitted_users
    ]
    submitted_users = [p.recipient for p in valid_pairs]
    feedback_user_gets = {}
    feedback_user_gives = {}
    for pair in valid_pairs:
        feedback_user_gives.setdefault(pair.grader.id, 0)
        # all valid recipients should be included in the givers list
        feedback_user_gives.setdefault(pair.recipient.id, 0)
        feedback_user_gives[pair.grader.id] += 1
        feedback_user_gets.setdefault(pair.recipient.id, 0)
        feedback_user_gets[pair.recipient.id] += 1

    # consider only valid submitters for pairing
    feedback_user_gives = {
        k: v for k, v in feedback_user_gives.items() if k in feedback_user_gets.keys()
    }

    # create new pairings
    pairs_created = 0
    for grader in submitted_users:
        if feedback_user_gives[grader.id] >= pairs:
            continue
        # filter out the users who are already paired with the grader
        submitted_ids = [user.id for user in submitted_users]
        already_paired = Pairing.query.filter(
            Pairing.course_id == course_id,
            Pairing.assignment_id == assignment_id,
            Pairing.grader_id == grader.id,
            Pairing.recipient_id.in_(submitted_ids),
        ).all()
        already_paired_ids = [p.recipient_id for p in already_paired]
        unpaired_with_grader = [
            user
            for user in submitted_users
            if user.id not in already_paired_ids and user.id != grader.id
        ]
        if len(unpaired_with_grader) == 0:
            print(
                "Couldn't find an unique partner for user {0}. Skipping".format(
                    grader.id
                )
            )
            continue

        pairs_needed = pairs - feedback_user_gives[grader.id]
        for i in range(pairs_needed):
            # select the users who are getting the minimum no.of feedback
            unpaired_ids = [user.id for user in unpaired_with_grader]
            feedback_unpaired_gets = {
                k: v for k, v in feedback_user_gets.items() if k in unpaired_ids
            }
            available_submitters = [
                user
                for user in unpaired_with_grader
                if feedback_unpaired_gets[user.id]
                == min(feedback_unpaired_gets.values())
            ]
            recipient = choice(available_submitters)

            print("Creating pair {0} => {1}".format(grader.id, recipient.id))
            try:
                pair = create_pairing(teacher, grader, recipient, course, assignment)
            except (errors.PairingExists, errors.PairingToSelf):
                continue
            send_pairing_email.queue(pair.id)
            feedback_user_gets[recipient.id] += 1
            feedback_user_gives[grader.id] += 1
            pairs_created += 1

    print("Created {0} new pairings.".format(pairs_created))


@rq.job("low")
def add_missing_pairings(course_id, assignment_id, min_pairs):
    """A job to fill the pairs lost during the `replace_unsubmitted_pairs`. In
    the previous job, the pairs weren't categorized as regular pairs and extra
    review pairs. So the number of pairs created were not the same as the number
    of pairs removed from each student, as the extra reviews they had given were
    counted into the regular pairs as well.

    This function get the pairs for each student and fills in the missing pairs
    which were left out due the miscounting in the previous job.

    :param course_id: canvas id of the course
    :param assignment_id: canvas id of the assignment
    :param min_pairs: the minimum no.of pairs that should be assigned to each
        student without including the extra reviews
    :return: None
    """
    teacher = get_course_teacher(course_id)
    canvas = get_canvas_client(teacher.canvas_access_token)
    course = canvas.get_course(course_id)
    assignment = course.get_assignment(assignment_id)
    submissions = assignment.get_submissions()
    submitted = [sub for sub in submissions if sub.workflow_state != "unsubmitted"]
    all_canvas_ids = [s.user_id for s in submissions]
    submitted_canvas_ids = [s.user_id for s in submitted]

    pairs = Pairing.query.filter(
        Pairing.course_id == course_id,
        Pairing.assignment_id == assignment_id,
        # grader_id == creator_id for extra pairs
        Pairing.grader_id != Pairing.creator_id,
    ).all()
    all_students = User.query.filter(User.canvas_id.in_(all_canvas_ids)).all()
    submitted_users = [s for s in all_students if s.canvas_id in submitted_canvas_ids]
    feedback_user_gets = {s.id: 0 for s in submitted_users}
    for pair in pairs:
        feedback_user_gets.setdefault(pair.recipient_id, 0)
        feedback_user_gets[pair.recipient_id] += 1

    pairs_created = 0
    for grader in all_students:
        already_paired_users = [
            pair.recipient_id for pair in pairs if pair.grader_id == grader.id
        ]
        missing_pairs = min_pairs - len(already_paired_users)
        if missing_pairs <= 0:
            continue

        unpaired_users = [
            user
            for user in submitted_users
            if user.id not in already_paired_users and user.id != grader.id
        ]
        if len(unpaired_users) == 0:
            print("Couldn't find a submitter to pair user {}".format(grader.id))
            continue

        for i in range(missing_pairs):
            unpaired_ids = [user.id for user in unpaired_users]
            feedback_unpaired_gets = {
                k: v for k, v in feedback_user_gets.items() if k in unpaired_ids
            }
            available_submitters = [
                user
                for user in unpaired_users
                if feedback_unpaired_gets[user.id]
                == min(feedback_unpaired_gets.values())
            ]
            recipient = choice(available_submitters)

            print("Creating pair {0} => {1}".format(grader.id, recipient.id))
            try:
                pair = create_pairing(teacher, grader, recipient, course, assignment)
            except (errors.PairingToSelf, errors.PairingExists):
                continue
            unpaired_users.remove(recipient)
            send_pairing_email.queue(pair.id)
            feedback_user_gets[recipient.id] += 1
            pairs_created += 1

    print("Created {0} new pairs".format(pairs_created))


@rq.job("low")
def fix_user_emails():
    """Some users have the user ID as the emails as they do not have a email,
    on record on canvas. This job appends the domain @gatech.edu to the emails
    that are not properly email address formatted.
    """
    users = User.query.all()
    for user in users:
        user.email = proper_email(user)
        user.save()


@rq.job("low")
def update_real_name_from_canvas():
    """A background that gets the name of the students from canvas and updates
    the local user model's real_name field.
    """
    course_ids = db.session.query(Pairing.course_id).distinct().all()
    for course_id in course_ids:
        course_id = course_id[0]
        teacher = get_course_teacher(course_id)
        canvas = get_canvas_client(teacher.canvas_access_token)
        course = canvas.get_course(course_id, include=["public_description"])
        users = course.get_users()

        for user in users:
            local_user = User.query.filter_by(canvas_id=user.id).first()
            if local_user.real_name != user.name:
                local_user.real_name = user.name
                db.session.add(local_user)

        db.session.commit()
