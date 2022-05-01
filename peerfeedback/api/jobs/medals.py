from sentry_sdk import capture_message
from sqlalchemy.orm import joinedload

from peerfeedback.models import Pairing, Feedback, Task, Notification, Comment, Medal
from peerfeedback.extensions import rq


@rq.job("low")
def award_super_commentator(comment_id):
    comment = Comment.query.options(joinedload(Comment.likes)).get(comment_id)
    if not comment:
        capture_message("Invalid comment id: {0}".format(comment_id))
        return

    if len(comment.likes) < 10:
        return

    medal = Medal.create(name="Super Commentator", user_id=comment.commenter_id)
    medal.save()

    notification = Notification.create(
        read=False,
        item=Notification.MEDAL,
        item_id=medal.id,
        course_name=comment.course_name,
        course_id=comment.course_id,
        assignment_id=comment.assignment_id,
        assignment_name=comment.assignment_name,
        recipient_id=comment.recipient_id,
    )
    notification.save()


@rq.job("low")
def award_contributor_medal(feedback_id):
    feed = Feedback.query.get(feedback_id)
    if not feed:
        capture_message("Invalid feedback id: {0}".format(feedback_id))
        return

    awarded = Medal.query.filter_by(
        name="Contributor", user_id=feed.reviewer_id
    ).first()
    if awarded:
        return

    medal = Medal.create(name="Contributor", user_id=feed.reviewer_id)
    medal.save()

    notification = Notification.create(
        read=False,
        item=Notification.MEDAL,
        item_id=medal.id,
        course_name=feed.course_name,
        course_id=feed.course_id,
        assignment_id=feed.assignment_id,
        assignment_name=feed.assignment_name,
        recipient_id=feed.reviewer_id,
        user_id=feed.receiver_id,
    )
    notification.save()


@rq.job("low")
def award_generous_reviewer_medal(user_id):
    awarded = Medal.query.filter_by(name="Generous Reviewer", user_id=user_id).first()
    if awarded:
        return

    pairings = (
        Pairing.query.filter_by(grader_id=user_id, creator_id=user_id)
        .options(joinedload(Pairing.task))
        .all()
    )
    if len(pairings) < 10:
        return

    all_complete = all([pair.task.status == Task.COMPLETE for pair in pairings])
    if not all_complete:
        return

    medal = Medal.create(name="Generous Reviewer", user_id=user_id)
    medal.save()

    notification = Notification.create(
        read=False, item=Notification.MEDAL, item_id=medal.id, user_id=user_id
    )
    notification.save()
