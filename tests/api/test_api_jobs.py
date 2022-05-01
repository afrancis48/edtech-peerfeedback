import pytest

from unittest.mock import patch

from peerfeedback.models import Feedback, Notification, Comment
from peerfeedback.api.jobs.notifications import notify_discussion_participants
from peerfeedback.api.jobs.feedback import reopen_submitted_feedback


@pytest.fixture
def feedbacks(users, student):
    participants = users[1:8]
    feedbacks = []
    for p in participants:
        f = Feedback.create(
            course_id=1,
            assignment_id=1,
            receiver_id=student.id,
            reviewer_id=p.id,
            draft=False,
        )
        feedbacks.append(f)

    yield feedbacks

    for f in feedbacks:
        f.delete()


def create_comment(commenter, recipient):
    return Comment.create(
        value="Teacher comments on the submission",
        course_id=1,
        assignment_id=1,
        commenter_id=commenter.id,
        recipient_id=recipient.id,
    )


class TestNotifyDiscussionParticipants(object):
    """
    FUNCTION    notify_discussion_participants
    """

    def test_creates_notifications_for_all_users_who_have_submitted_feedback(
        self, db, feedbacks, student
    ):
        """
        GIVEN   some users have given feedback to a submission
        WHEN    function is called with the id of a comment posted on the submission
        THEN    all the users who have previously posted feedback and the owner
                of the submission get a notification
        """
        comment = create_comment(feedbacks[0].reviewer, student)
        assert 0 == db.session.query(Notification).count()
        notify_discussion_participants(comment.id)
        # notification count equals participants - commenter + owner
        assert len(feedbacks) == db.session.query(Notification).count()
        Notification.query.delete()

        # When on feedback is in draft = not submitted
        unsubmitted = feedbacks[-1]
        unsubmitted.draft = True
        unsubmitted.save()
        assert 0 == db.session.query(Notification).count()
        notify_discussion_participants(comment.id)
        assert len(feedbacks) - 1 == db.session.query(Notification).count()
        Notification.query.delete()

        comment.delete()

    def test_notification_is_not_created_for_the_commenter(
        self, db, feedbacks, student
    ):
        """
        GIVEN   some users have given feedback to a submission
        WHEN    function is called with the id of the comment
        THEN    the notification is created for all participants except
                the person who posted the comment
        """
        commenter = feedbacks[1].reviewer
        comment = create_comment(commenter, student)
        assert (
            0
            == db.session.query(Notification)
            .filter(Notification.recipient_id == commenter.id)
            .count()
        )
        notify_discussion_participants(comment.id)
        assert (
            0
            == db.session.query(Notification)
            .filter(Notification.recipient_id == commenter.id)
            .count()
        )
        Notification.query.delete()

    def test_notification_is_created_for_submission_owner(self, db, feedbacks, student):
        """
        GIVEN   some users have given feedback to a submission
        WHEN    function is called with the id of the comment
        THEN    the notification is created for the submitter
        """
        commenter = feedbacks[1].reviewer
        comment = create_comment(commenter, student)
        assert (
            0
            == db.session.query(Notification)
            .filter(Notification.recipient_id == student.id)
            .count()
        )
        notify_discussion_participants(comment.id)
        assert (
            1
            == db.session.query(Notification)
            .filter(Notification.recipient_id == student.id)
            .count()
        )
        Notification.query.delete()

    def test_does_nothing_if_invalid_comment_id_is_passed(self, db):
        """
        GIVEN   the app is setup
        WHEN    a invalid comment id is passed to the job
        THEN    the job does not create any notifications
        """
        assert 0 == db.session.query(Notification).count()
        notify_discussion_participants(40)
        assert 0 == db.session.query(Notification).count()


class TestChangeAssignmentRubric(object):
    """
    FUNCTION    reopen_submitted_feedback(assignment_id, rubric_id, send_emails=False)
    """

    def test_changes_the_rubric_id_of_all_feedback(
        self, rubric, feedback, task, ta_task
    ):
        """
        GIVEN   the app all ready has a number of feedback for an assignment
        WHEN    the function is called with a rubric_id
        THEN    all the feedback are reset to that rubric id
        """
        reopen_submitted_feedback(1, rubric.id)
        for f in feedback:
            assert f.rubric_id == rubric.id

    def test_does_not_change_anything_if_invalid_rubric_id_is_sent(
        self, feedback, rubric
    ):
        """
        GIVEN   the app is with a set of feedback
        WHEN    the function is called with the ID of a non existent rubric id
        THEN    nothing is changed in the feedback
        """
        for f in feedback:
            f.update(rubric_id=rubric.id)
        reopen_submitted_feedback(1, 23)
        for f in feedback:
            assert f.rubric_id != 23

    def test_clears_previous_grades_from_feedback_on_rubric_change(
        self, feedback, rubric, task, ta_task
    ):
        """
        GIVEN   there are feedback with grades in the app for an assignment
        WHEN    the function is called with the id of a new rubric
        THEN    the old grades are discarded
        """
        for f in feedback:
            f.update(grades=[{"criteria": "Criteria 1", "level": 3}])
        reopen_submitted_feedback(1, rubric.id)
        for f in feedback:
            assert f.grades == []

    @patch("peerfeedback.api.jobs.feedback.send_redo_rubric_emails")
    def test_email_area_sent_to_the_submitted_feedback(
        self, mock_email, feedback, rubric, task, ta_task
    ):
        """
        GIVEN   there are feedback which have been submitted
        WHEN    the rubric for the assignment is changed
        THEN    emails are sent to the people who have submitted the feedback
        """
        reopen_submitted_feedback(1, rubric.id, send_emails=True)
        assert mock_email.call_count == len(feedback)
