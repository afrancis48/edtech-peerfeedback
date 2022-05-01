from sqlalchemy.orm import joinedload

from peerfeedback.models import Feedback, Notification, Comment
from peerfeedback.extensions import rq


@rq.job("default")
def notify_discussion_participants(comment_id):
    """Background job which posts a notification for all the participants of a
    discussion. Participants = people who have submitted feedback.

    :param comment_id: id of the comment created
    """
    comment = Comment.query.get(comment_id)
    if not comment:
        return
    feedbacks = (
        Feedback.query.filter(
            Feedback.course_id == comment.course_id,
            Feedback.assignment_id == comment.assignment_id,
            Feedback.receiver_id == comment.recipient_id,
            Feedback.draft.is_(False),
        )
        .options(joinedload(Feedback.reviewer))
        .all()
    )
    participants = [
        f.reviewer for f in feedbacks if f.reviewer_id != comment.commenter_id
    ]

    if comment.recipient_id != comment.commenter_id:
        participants.append(comment.recipient)

    for p in participants:
        Notification.create(
            item=Notification.COMMENT,
            item_id=comment.id,
            course_name=comment.course_name,
            course_id=comment.course_id,
            assignment_name=comment.assignment_name,
            assignment_id=comment.assignment_id,
            user_id=comment.recipient_id,
            recipient_id=p.id,
            notifier_id=comment.commenter_id,
        )
