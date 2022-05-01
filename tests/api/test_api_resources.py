# -*- coding: utf-8 -*-
"""Tests for REST API endpoints defined in api.resource"""
import json
import datetime
import pytest

from unittest.mock import patch

from peerfeedback.models import (
    Pairing,
    Feedback,
    Task,
    Notification,
    AssignmentSettings,
    MetaFeedback,
    Comment,
    ExtraFeedback,
)
from peerfeedback.api import errors

from tests.factories import token


@pytest.fixture
def settings(db):
    settings = AssignmentSettings.create(
        assignment_id=1,
        course_id=1,
        allow_student_pairing=True,
        max_reviews=10,
        use_rubric=False,
    )
    yield settings
    settings.delete()


@pytest.fixture
def task(pairing):
    t = Task.create(
        status=Task.PENDING,
        course_id=1,
        course_name="Test Course",
        assignment_id=1,
        assignment_name="Test Assignment",
        user_id=pairing.grader_id,
        pairing_id=pairing.id,
    )
    yield t
    t.delete()


@pytest.fixture
def feedback(task):
    pairing = task.pairing
    f = Feedback.create(
        type=Feedback.STUDENT,
        value="Good work.",
        grades=[],
        draft=True,
        submission_id=105,
        assignment_name="Test Assignment",
        assignment_id=1,
        course_name="Demo Course",
        course_id=1,
        receiver_id=pairing.recipient_id,
        reviewer_id=pairing.grader_id,
        pairing_id=pairing.id,
    )
    yield f
    f.delete()


@pytest.mark.usefixtures("users", "settings")
class TestFeedbackResource(object):
    """
    URL     /api/feedback/
            /api/feedback/<id>/
    """

    def test_get_returns_feedback_object(self, db, client, student, feedback):
        """
        GIVEN   a feedback exists with a ID
        WHEN    a get request is made with the feedback's ID
        THEN    the feedback is returned as JSON
        """
        response = client.get(
            "/api/feedback/{0}/".format(feedback.id), headers=token(student)
        )
        assert 200 == response.status_code
        assert feedback.id == response.get_json()["id"]

    def test_get_throws_404_for_invalid_id(self, client, student):
        """
        GIVEN   there exists no feedback with a specified ID
        WHEN    a get request is made with non-existent id
        THEN    a 404 error is returned
        """
        response = client.get("/api/feedback/10/", headers=token(student))
        assert 404 == response.status_code

    def test_put_updates_passed_on_values(self, client, feedback):
        """
        GIVEN   a feedback exists with a specific id
        WHEN    a put request to that feedback ID is made
        THEN    the feedback object is updated to reflect the request
        """
        response = client.put(
            "/api/feedback/{0}/".format(feedback.id),
            data=json.dumps(dict(read_time=30, write_time=20)),
            content_type="application/json",
            headers=token(feedback.reviewer),
        )
        assert 200 == response.status_code
        assert 30 == feedback.read_time
        assert 20 == feedback.write_time

    def test_put_returns_404_for_non_existing_feedback(self, client, student):
        """
        GIVEN   there is no feedback with a specific id
        WHEN    a put request is made to update the non-existent feedback
        THEN    a 404 error is returned
        """
        response = client.put("/api/feedback/10/", headers=token(student))
        assert 404 == response.status_code

    def test_put_does_not_update_published_feedback(self, client, feedback):
        """
        GIVEN   the feedback has been submitted with draft set to false
        WHEN    a put request is made to update the value of its attributes
        THEN    a error is returned without updating the feedback
        """
        feedback.draft = False
        feedback.save()

        response = client.put(
            "/api/feedback/{0}/".format(feedback.id),
            data=json.dumps(dict(read_time=40)),
            headers=token(feedback.reviewer),
        )
        assert 400 == response.status_code
        assert 40 != feedback.read_time

    def test__first_put_sets_start_time_of_corresponding_task(
        self, db, client, task, feedback
    ):
        """
        GIVEN   there exists a pairing with task
        WHEN    the user updates the feedback for the first time using PUT
        THEN    the task start time is set to the feedback creation time
        """
        data = {
            "course_id": 1,
            "assignment_id": 1,
            "receiver_id": task.pairing.recipient_id,
        }
        assert task.start_date is None
        response = client.put(
            f"/api/feedback/{feedback.id}/",
            data=json.dumps(data),
            content_type="application/json",
            headers=token(task.user),
        )
        assert 200 == response.status_code
        assert task.start_date

    @patch("peerfeedback.api.resource.award_contributor_medal")
    @patch("peerfeedback.api.resource.award_generous_reviewer_medal")
    def test_put_sets_done_time_of_corresponding_task(
        self, cm, rm, client, task, feedback
    ):
        """
        GIVEN   there is a feedback in draft state
        WHEN    the feedback is published with a put request
        THEN    the corresponding task state is set to complete with done date
        """
        assert task.done_date is None
        response = client.put(
            "/api/feedback/{0}/".format(feedback.id),
            data=json.dumps(dict(draft=False)),
            content_type="application/json",
            headers=token(feedback.reviewer),
        )
        assert 200 == response.status_code
        assert Task.COMPLETE == task.status
        assert task.done_date is not None
        cm.queue.assert_called_once()
        rm.queue.assert_called_once()


@pytest.mark.usefixtures("users")
class TestTaskResource(object):
    """
    URL     /api/task/
            /api/task/<id>/
    """

    time = datetime.datetime.now()
    task = {
        "status": Task.PENDING,
        "course_id": 1,
        "course_name": "Demo course",
        "assignment_id": 3,
        "assignment_name": "Test Assignment",
        "start_date": time,
        "due_date": time,
        "done_date": time,
    }

    def test_put_updates_task_status(self, db, client, teacher):
        """
        GIVEN   a task exists with a specific ID
        WHEN    a put request is sent with updated params
        THEN    the task is modified with the data from PUT request
        """
        t = Task.create(**self.task)
        response = client.put(
            "/api/task/{0}/".format(t.id),
            data=dict(status="COMPLETE"),
            headers=token(teacher),
        )
        assert 200 == response.status_code
        assert "COMPLETE" == response.get_json()["status"]

    def test_put_returns_404_for_invalid_id(self, client, teacher):
        """
        GIVEN   there is no task with a specific ID
        WHEN    a put request is sent with the non existent ID
        THEN    a 404 not found error is returned
        """
        response = client.put(
            "/api/task/10/", data=dict(status="COMPLETE"), headers=token(teacher)
        )
        assert 404 == response.status_code

    def test_put_returns_400_for_invalid_status_string(self, client, teacher):
        """
        GIVEN   the task needs updating
        WHEN    a put request is sent with a non compatible status flag
        THEN    a 400 error is returned
        """
        response = client.put(
            "/api/task/10/", data=dict(status="INVALID_STATUS"), headers=token(teacher)
        )
        assert 400 == response.status_code
        assert "not a valid choice" in response.data.decode()


@pytest.mark.usefixtures("users", "setup_coursemap")
class TestPairingResource(object):
    """
    URL     /api/pairing/
            /api/pairing/<id>/
    """

    data = {
        "type": Pairing.STUDENT,
        "course_id": 1,
        "assignment_id": 1,
        "recipient_id": 3,
    }

    def test_get_returns_pairing_matching_id(self, db, client, student, pairing):
        """
        GIVEN   a pairing object with id
        WHEN    a get request is made with the id
        THEN    the pairing is returned as JSON
        """
        response = client.get(
            "/api/pairing/{0}/".format(pairing.id), headers=token(student)
        )
        assert 200 == response.status_code
        assert "id" in response.get_json()
        assert "grader" in response.get_json()

    def test_get_throws_404_for_invalid_id(self, client, student):
        """
        GIVEN   the is no pairing with a given ID
        WHEN    a get request is sent with the non existent ID
        THEN    a 404 error is returned
        """
        response = client.get("/api/pairing/999/", headers=token(student))
        assert 404 == response.status_code

    def test_get_has_nested_objects_in_response(self, client, student, pairing):
        """
        GIVEN   there exists a pairing
        WHEN    a get request is made with the pairing ID
        THEN    then the pairing is returned with grader, recipient nested objects
        """
        response = client.get(
            "/api/pairing/{0}/".format(pairing.id), headers=token(student)
        )
        data = response.get_json()
        assert isinstance(data["grader"], dict)
        assert isinstance(data["recipient"], dict)

    def test_post_throws_400_when_missing_parameters(self, client, teacher):
        """
        GIVEN   the course is initialized with assignment settings
        WHEN    required params are missing in the post request
        THEN    a 400 error is returned
        """
        data_sets = [
            {},  # Missing everything
            {"course_id": 1},  # Missing assign, grader, recipient
            {"course_id": 1, "assignment_id": 2},  # Missing grader and recipient
            {"course_id": 1, "assignment_id": 2, "grader_id": 2},  # Missing recipient
            {"course_id": 1, "assignment_id": 2, "recipient": 3},  # Missing Grader
        ]

        for data in data_sets:
            response = client.post(
                "/api/pairing/",
                data=json.dumps(data),
                content_type="application/json",
                headers=token(teacher),
            )
            assert 400 == response.status_code

    def test_post_throws_400_when_assignment_is_not_activated(self, client, student):
        """
        GIVEN   the course is not setup
        WHEN    a post request is made to create a pairing
        THEN    a 400 error is returned
        """
        response = client.post(
            "/api/pairing/",
            data=json.dumps(self.data),
            content_type="application/json",
            headers=token(student),
        )
        assert 400 == response.status_code
        assert errors.ASSIGNMENT_NOT_SETUP in response.data.decode()

    def test_post_throws_400_when_pairing_reaches_review_limit(
        self, client, student, settings
    ):
        """
        GIVEN   the max reviews limit is set in the assignment settings
        WHEN    a post request is made making the pairs exceed the limit
        THEN    a 400 error is returned with the message
        """
        settings.max_reviews = 0
        settings.save()
        response = client.post(
            "/api/pairing/",
            data=json.dumps(self.data),
            content_type="application/json",
            headers=token(student),
        )
        assert 400 == response.status_code
        assert errors.MAX_LIMIT_REACHED in response.data.decode()

    def test_post_throws_409_for_existing_pairing(
        self, client, settings, paired_students
    ):
        """
        GIVEN   there is an existing pair of grader and recipient for an assignment
        WHEN    a post request is made to create a new pairing for the same students
        THEN    a 409 conflict error is returned
        """
        grader, recipient = paired_students
        data = {"course_id": 1, "assignment_id": 1, "recipient_id": recipient.id}
        response = client.post(
            "/api/pairing/",
            data=json.dumps(data),
            content_type="application/json",
            headers=token(grader),
        )
        assert 409 == response.status_code

    def test_post_throws_400_for_same_grader_recipient(self, client, student, settings):
        """
        GIVEN   the assignment is initialized
        WHEN    a post request is sent with the grader set same as recipient
        THEN    an error is returned with message
        """
        data = dict(
            course_id=1,
            course_name="Course",
            assignment_id=1,
            assignment_name="Test",
            recipient_id=student.id,
        )
        response = client.post(
            "/api/pairing/",
            data=json.dumps(data),
            content_type="application/json",
            headers=token(student),
        )
        assert 400 == response.status_code
        assert errors.GRADER_RECIPIENT_SAME in response.data.decode()

    def test_post_creates_pairing_and_task(self, client, student, settings):
        """
        GIVEN   the assignment is setup
        WHEN    a post request creates the pairing
        THEN    a task should also be created along with the pairing
        """
        assert 0 == len(Pairing.query.all())
        assert 0 == len(Task.query.all())
        response = client.post(
            "/api/pairing/",
            data=json.dumps(self.data),
            content_type="application/json",
            headers=token(student),
        )
        assert 201 == response.status_code
        pairings = Pairing.query.all()
        assert 1 == len(pairings)
        assert 1 == len(Task.query.all())
        assert 1 == pairings[0].course_id
        assert 1 == pairings[0].assignment_id

    def test_post_creates_pairing_with_type_student_when_not_supplied(
        self, client, student, settings
    ):
        """
        GIVEN   the assignment is setup
        WHEN    a post request is made to create a pairing without specifying its type
        THEN    automatically set the pairing type to student pairing
        """
        data = {"course_id": 1, "assignment_id": 1, "recipient_id": 5}

        response = client.post(
            "/api/pairing/",
            data=json.dumps(data),
            content_type="application/json",
            headers=token(student),
        )
        assert 201 == response.status_code
        pairing = Pairing.query.first()
        assert pairing.type == Pairing.STUDENT

    def test_put_archives_pairing_and_task(self, client, teacher, pairing, task):
        """
        GIVEN   a pairing with task exists
        WHEN    a put request is made to archive the pairing
        THEN    the pairing and the task are both archived
        """
        assert task.status == Task.PENDING
        assert pairing.archived is False
        res = client.put(
            f"/api/pairing/{pairing.id}/",
            data=json.dumps(dict(archived=True)),
            content_type="application/json",
            headers=token(teacher),
        )
        assert 200 == res.status_code
        assert pairing.archived == True
        assert task.status == Task.ARCHIVED

    def test_put_can_unarchive_a_pairing_and_task(self, client, teacher, pairing, task):
        """
        GIVEN   there is an archived pairing and associated task
        WHEN    a put request is made to unarchive the pairing
        THEN    the both the pairing and the task are unarchived
        """
        task.status = Task.ARCHIVED
        task.save()
        pairing.archived = True
        pairing.save()
        res = client.put(
            f"/api/pairing/{pairing.id}/",
            data=json.dumps(dict(archived=False)),
            content_type="application/json",
            headers=token(teacher),
        )
        assert 200 == res.status_code
        assert task.status == Task.PENDING
        assert pairing.archived is False

    def test_archiving_cannot_be_done_by_students(self, client, pairing, student):
        """
        GIVEN   a pairing exists
        WHEN    a put request is made to archive the pairing by a student
        THEN    a 403 error is returned
        """
        res = client.put(
            f"/api/pairing/{pairing.id}/",
            data=json.dumps(dict(archived=True)),
            content_type="application/json",
            headers=token(student),
        )
        assert 403 == res.status_code

    def test_put_returns_404_for_an_invalid_pairing_id(self, client, teacher):
        """
        GIVEN   the course is setup
        WHEN    a request is made to change a non-existent pairing
        THEN    a 404 not-found response is returned
        """
        res = client.put(
            f"/api/pairing/1235/",
            data=json.dumps(dict(archived=True)),
            content_type="application/json",
            headers=token(teacher),
        )
        assert 404 == res.status_code


@pytest.mark.usefixtures("users", "setup_coursemap")
class TestAssignmentSettings(object):
    """
    URL     /api/assignment/settings/
            /api/assignment/settings/<id>/
    """

    def test_put_updates_data(self, db, client, teacher, settings):
        """
        GIVEN   the settings has been setup for an assignment
        WHEN    a put request is sent by the teacher
        THEN    the settings is updated
        """
        data = dict(
            course_id=1, assignment_id=1, allow_student_pairing=False, max_reviews=0
        )
        response = client.put(
            "/api/assignment/settings/{0}/".format(settings.id),
            content_type="application/json",
            data=json.dumps(data),
            headers=token(teacher),
        )
        assert 200 == response.status_code
        assert 0 == response.get_json()["max_reviews"]

    def test_put_rejects_request_by_student(self, client, student, settings):
        """
        GIVEN   the settings have been setup for an assignment
        WHEN    a student makes a put request
        THEN    a 403 forbidden error is returned
        """
        data = dict(
            course_id=1, assignment_id=1, allow_student_pairing=False, max_reviews=0
        )
        response = client.put(
            "/api/assignment/settings/{0}/".format(settings.id),
            content_type="application/json",
            data=json.dumps(data),
            headers=token(student),
        )
        assert 403 == response.status_code

    def test_put_throws_404_for_invalid_settings_id(self, client, teacher):
        """
        GIVEN   there is no assignment settings with a given ID
        WHEN    a put request is made with the non-existent settings ID
        THEN    a 404 error is returned
        """
        data = dict(
            assignment_id=1, course_id=1, allow_student_pairing=False, max_reviews=0
        )
        response = client.put(
            "/api/assignment/settings/10/",
            content_type="application/json",
            data=json.dumps(data),
            headers=token(teacher),
        )
        assert 404 == response.status_code


@pytest.mark.usefixtures("users")
class TestMetaFeedback(object):
    """
    URL     /api/feedback/meta/
            /api/feedback/meta/<id>/
    """

    def test_get_returns_meta_for_a_given_feedback(self, db, client, teacher):
        """
        GIVEN   a meta feedback exists with the a id
        WHEN    a get request is sent with the ID
        THEN    the meta feedback is sent back as JSON
        """
        feedback = Feedback.create()
        meta = MetaFeedback.create(
            points=5,
            comment="Good",
            feedback_id=feedback.id,
            receiver_id=3,
            reviewer_id=2,
        )
        r = client.get(
            "/api/feedback/meta/{0}/".format(meta.id), headers=token(teacher)
        )
        assert 200 == r.status_code
        assert "Good" == json.loads(r.data.decode())["comment"]

    def test_get_returns_404(self, client, teacher):
        """
        GIVEN   there is no meta feedback with a specific ID
        WHEN    a get request is sent with the non existent ID
        THEN    a 404 error is returned
        """
        r = client.get("/api/feedback/meta/10/", headers=token(teacher))
        assert 404 == r.status_code

    def test_post_adds_meta_feedback(self, client, teacher):
        """
        GIVEN   the database is setup
        WHEN    a post request is sent to with the params
        THEN    a new meta feedback is saved in the DB
        """
        feedback = Feedback.create()
        metas = len(MetaFeedback.query.all())
        data = dict(
            feedback_id=feedback.id, points=5, comment="", receiver_id=3, reviewer_id=2
        )
        r = client.post(
            "/api/feedback/meta/",
            data=json.dumps(data),
            content_type="application/json",
            headers=token(teacher),
        )
        assert 201 == r.status_code
        assert 5 == json.loads(r.data.decode())["points"]
        assert metas + 1 == len(MetaFeedback.query.all())

    def test_post_returns_400_for_missing_info(self, client, teacher):
        """
        GIVEN   the app is setup
        WHEN    a post request is made without required params
        THEN    a 400 error is returned
        """
        data = dict(points=10, comment="", receiver_id=3)  # missing feedback.id
        r = client.post(
            "/api/feedback/meta/",
            data=json.dumps(data),
            content_type="application/json",
            headers=token(teacher),
        )
        assert 400 == r.status_code

        feedback = Feedback.create()
        data = dict(feedback_id=feedback.id, points=10, comment="")
        r = client.post(
            "/api/feedback/meta/",
            data=json.dumps(data),
            content_type="application/json",
            headers=token(teacher),
        )
        assert 400 == r.status_code

    def test_post_returns_error_when_points_are_not_between_limits(
        self, client, student
    ):
        """
        GIVEN   the database is setup
        WHEN    a request is sent with points outside of the allowed region
        THEN    an 400 error returned
        """
        feedback = Feedback.create()
        existing = len(MetaFeedback.query.all())
        data = dict(
            feedback_id=feedback.id, points=10, comment="", receiver_id=3, reviewer_id=2
        )
        r = client.post(
            "/api/feedback/meta/",
            data=json.dumps(data),
            content_type="application/json",
            headers=token(student),
        )
        assert 400 == r.status_code
        assert existing == len(MetaFeedback.query.all())


@pytest.mark.usefixtures("users")
class TestNotificationResource(object):
    """
    URL     /api/notification/<id>/
    """

    def test_put_marks_the_notification_read(self, db, client, paired_students):
        """
        GIVEN   there is a notification in the DB
        WHEN    a put request is sent with the read status
        THEN    the notification is updated with the read status
        """
        grader, recipient = paired_students
        note = Notification.create(user_id=recipient.id, notifier_id=grader.id)
        assert not note.read

        response = client.put(
            "/api/notification/{0}/".format(note.id),
            data=dict(read=True),
            headers=token(recipient),
        )
        assert 200 == response.status_code
        assert note.read

    def test_put_returns_404_for_non_existent_notifications(self, client, student):
        """
        GIVEN   no notification exists for a given ID
        WHEN    a put request is made with that ID
        THEN    a 404 error is returned
        """
        response = client.put(
            "/api/notification/99/", data=dict(read=True), headers=token(student)
        )
        assert 404 == response.status_code


@pytest.mark.usefixtures("users")
class TestCommentResource(object):
    """
    URL     /api/comment/
    """

    @patch("peerfeedback.api.resource.notify_discussion_participants")
    def test_post_accepts_only_from_paired_students_who_completed_feedback(
        self, pjob, client, feedback
    ):
        """
        METHOD  post
        GIVEN   a user has been paired with another and has submitted his feedback
        WHEN    the graders makes a post request to add a comment
        THEN    a new comment should be created
        """
        data = {
            "course_id": feedback.course_id,
            "assignment_id": feedback.assignment_id,
            "recipient_id": feedback.receiver_id,
            "value": "Test comment",
        }
        r = client.post(
            "/api/comment/",
            data=json.dumps(data),
            content_type="application/json",
            headers=token(feedback.reviewer),
        )
        assert 400 == r.status_code

        feedback.draft = False
        feedback.save()
        r = client.post(
            "/api/comment/",
            data=json.dumps(data),
            content_type="application/json",
            headers=token(feedback.reviewer),
        )
        assert 201 == r.status_code
        assert "Test comment" == r.get_json()["value"]

    @patch("peerfeedback.api.resource.notify_discussion_participants")
    def test_course_name_set_in_the_comment_without_passing_as_param(
        self, pjob, client, feedback
    ):
        """
        METHOD  post
        GIVEN   the commenter has submitted the feedback
        WHEN    a new comment is created by a POST request without course_name in params
        THEN    the course name somehow is set in the saved comment (copies from tasks)
        """
        feedback.draft = False
        feedback.save()
        data = dict(
            value="Comment with Course name",
            course_id=1,
            assignment_id=1,
            recipient_id=feedback.receiver_id,
        )
        r = client.post(
            "/api/comment/",
            data=json.dumps(data),
            content_type="application/json",
            headers=token(feedback.reviewer),
        )
        assert 201 == r.status_code
        c = Comment.query.get(r.get_json()["id"])
        assert "Demo Course" == c.course_name

    def test_post_returns_error_if_student_is_not_paired(
        self, client, student, setup_coursemap
    ):
        """
        METHOD  post
        GIVEN   the course is setup
        WHEN    the user not paired with another user makes a POST request
        THEN    a 400 error is returned
        """
        data = dict(
            value="Comment that won't get saved",
            course_id=1,
            assignment_id=1,
            recipient_id=10,
        )
        r = client.post(
            "/api/comment/",
            data=json.dumps(data),
            content_type="application/json",
            headers=token(student),
        )
        assert 400 == r.status_code
        assert errors.NOT_PAIRED == r.get_json()["message"]

    @patch("peerfeedback.api.resource.notify_discussion_participants")
    def test_post_allows_teachers_and_tas_to_add_comments(
        self, pjob, client, teacher, ta, feedback
    ):
        """
        METHOD  post
        GIVEN   the course is setup and pairing is done with feedbacks generated
        WHEN    the teacher or a TA posts a comment to a assignment
        THEN    the comment is created
        """
        data = dict(
            value="Comment from people who moderate this application",
            course_id=1,
            assignment_id=1,
            recipient_id=10,
        )
        r = client.post(
            "/api/comment/",
            data=json.dumps(data),
            content_type="application/json",
            headers=token(teacher),
        )
        assert 201 == r.status_code

        r = client.post(
            "/api/comment/",
            data=json.dumps(data),
            content_type="application/json",
            headers=token(ta),
        )
        assert 201 == r.status_code

    @patch("peerfeedback.api.resource.notify_discussion_participants")
    def test_post_allows_submission_owner_to_post_comments(
        self, pjob, client, feedback
    ):
        """
        METHOD  post
        GIVEN   the course is setup and feedback generated
        WHEN    the user posts a comment on own assignment
        THEN    the comment is created
        """
        data = dict(
            value="Own comment",
            course_id=1,
            assignment_id=1,
            recipient_id=feedback.receiver_id,
        )
        r = client.post(
            "/api/comment/",
            data=json.dumps(data),
            content_type="application/json",
            headers=token(feedback.receiver),
        )
        assert 201 == r.status_code

    @patch("peerfeedback.api.resource.notify_discussion_participants.queue")
    def test_post_notifies_all_discussion_members_on_comment_creation(
        self, pjob, client, feedback
    ):
        """
        METHOD  post
        GIVEN   the course is setup and feedback generated
        WHEN    the comment is created in the post request
        THEN    all the discussion participants are notified
        """
        data = dict(
            value="Own comment",
            course_id=1,
            assignment_id=1,
            recipient_id=feedback.receiver_id,
        )
        r = client.post(
            "/api/comment/",
            data=json.dumps(data),
            content_type="application/json",
            headers=token(feedback.receiver),
        )
        assert 201 == r.status_code
        pjob.assert_called_with(r.get_json()["id"])

    @patch("peerfeedback.api.resource.notify_discussion_participants")
    def test_post_returns_error_for_empty_comments(self, pjob, client, feedback):
        """
        METHOD  post
        GIVEN   the course is setup and feedback generated
        WHEN    the user posts a comment on own assignment
        THEN    the comment is created
        """
        data = dict(
            value="", course_id=1, assignment_id=1, recipient_id=feedback.receiver_id
        )
        r = client.post(
            "/api/comment/",
            data=json.dumps(data),
            content_type="application/json",
            headers=token(feedback.receiver),
        )
        assert 400 == r.status_code


class TestExtraFeedbackResource(object):
    """
    URL   /api/extra_feedback/
    """

    def test_post_adds_a_extra_feedback_request(self, client, student):
        """
        GIVEN   the student exists in the db
        WHEN    a post request is made to place an extra feedback request
        THEN    a new ExtraFeedback row is added to the DB for the given
                assignment
        """
        assert 0 == len(ExtraFeedback.query.all())
        data = {"course_id": 1, "assignment_id": 5}
        response = client.post(
            "/api/extra_feedback/", data=data, headers=token(student)
        )
        assert 201 == response.status_code
        items = ExtraFeedback.query.all()
        assert 1 == len(items)
        assert 1 == items[0].course_id
        assert 5 == items[0].assignment_id

    def test_post_returns_a_409_if_there_is_already_a_active_request(
        self, client, student
    ):
        """
        GIVEN   the student already has am active extra feedback request
        WHEN    a post request is made to place an extra feedback request
        THEN    the application returns a 409 conflict response
        """
        assert 1 == len(ExtraFeedback.query.all())
        data = {"course_id": 1, "assignment_id": 5}
        response = client.post(
            "/api/extra_feedback/", data=data, headers=token(student)
        )
        assert 409 == response.status_code
