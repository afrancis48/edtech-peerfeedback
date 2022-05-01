from peerfeedback.api.jobs.sendmail import send_redo_rubric_emails
from peerfeedback.models import Feedback, Task, Rubric
from peerfeedback.extensions import rq, db


@rq.job("default")
def reopen_submitted_feedback(assignment_id, rubric_id, send_emails=False):
    """Background job which changes the rubric id in all the feedback created
    for that assignment.

    :param assignment_id: canvas id of the assignment whose rubric has been changed
    :param rubric_id: id of the new rubric to be used
    :param send_emails: whether to send out emails or not
    """
    rubric = Rubric.query.get(rubric_id)
    if not rubric:
        print("Could not find rubric")
        return

    all = Feedback.query.filter(
        Feedback.assignment_id == assignment_id,
        Feedback.draft.is_(False),
        (Feedback.rubric_id != rubric_id) | (Feedback.rubric_id.is_(None)),
    ).all()

    for fb in all:
        fb.rubric_id = rubric_id
        fb.grades = []
        fb.draft = True
        task = Task.query.filter_by(pairing_id=fb.pairing_id).first()
        if task:
            task.status = Task.IN_PROGRESS
            db.session.add(task)
        if send_emails:
            send_redo_rubric_emails(fb)
        db.session.add(fb)
    db.session.commit()


@rq.job("default")
def disable_submitted_feedback_grades(assignment_id, old_rubric):
    """Job that removes the grades from all the feedback that has been submitted
    for the given assignment_id if it has used the old rubric

    :param assignment_id: Canvas id of the assignment
    :param old_rubric: id of the rubric whose grades need to be disabled
    """
    fbs = Feedback.query.filter(
        Feedback.assignment_id == assignment_id,
        Feedback.rubric_id == old_rubric,
        Feedback.draft.is_(False),
    ).all()

    for fb in fbs:
        fb.rubric_id = None
        fb.grades = []
        db.session.add(fb)
    db.session.commit()


@rq.job("default")
def change_rubric_on_unsubmitted_feedback(assignment_id, rubric_id):
    """Job that changes the rubric id of all unsubmitted feedback on the given
    assignment to the given rubric id

    :param assignment_id: canvas id of the assignment
    :param rubric_id: id of the new rubric to be set
    """
    if rubric_id and not Rubric.query.get(rubric_id):
        return

    fbs = Feedback.query.filter(
        Feedback.assignment_id == assignment_id, Feedback.draft.is_(True)
    ).all()

    for fb in fbs:
        fb.rubric_id = rubric_id
        db.session.add(fb)
    db.session.commit()
