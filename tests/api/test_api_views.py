# -*- coding: utf-8 -*-
"""Tests for the endpoints in api/views.py"""
import pytest

from unittest.mock import patch, Mock
from canvasapi.exceptions import ResourceDoesNotExist

from peerfeedback.models import User, Notification, Pairing
from tests.factories import token


class TestGetCourses(object):
    """
    FUNCTION    get_courses()
    URL         /courses/
    """

    def test_returns_users_courses(self, client, teacher):
        """
        GIVEN the flask application has access to Canvas API
        WHEN a GET request to /api/courses/ is sent
        THEN a list of courses is returned as JSON
        """
        resp = client.get("/api/courses/", headers=token(teacher))
        assert 200 == resp.status_code
        assert isinstance(resp.get_json(), list)

    @patch("peerfeedback.api.views.canvas.get_canvas_client")
    def test_returns_empty_list(self, mock_canvas, client, teacher):
        """
        GIVEN the canvas application returns no courses
        WHEN a GET request to /api/courses/ is sent
        THEN an empty list is returned as a JSON
        """
        mock_canvas.return_value.get_courses.return_value = []
        resp = client.get("/api/courses/", headers=token(teacher))
        assert 200 == resp.status_code
        assert resp.get_json() == []

    @patch("peerfeedback.api.views.canvas.get_canvas_client")
    def test_returns_error_on_canvas_connectivity_issue(self, canvas, client, teacher):
        """
        GIVEN the app encounters an exception when accessing the Canvas API
        WHEN a GET request to /api/courses/ is sent
        THEN the error message is returned as with a 500 status code
        """
        canvas.return_value.get_courses.side_effect = Mock(side_effect=ValueError())
        resp = client.get("/api/courses/", headers=token(teacher))
        assert 500 == resp.status_code
        assert "message" in resp.get_json()


class TestGetCourse(object):
    """
    FUNCTION    get_course
    URL         /api/course/<int:course_id>/
    """

    def test_returns_course_object(self, client, teacher):
        """
        GIVEN the application can connect to the Canvas API
        WHEN the get request is sent to the URL
        THEN the course object is returned in the JSON
        """
        resp = client.get("/api/course/1/", headers=token(teacher))
        assert 200 == resp.status_code
        course = resp.get_json()
        assert isinstance(course, dict)
        assert 1 == course["id"]

    @patch("peerfeedback.api.views.canvas.get_canvas_client")
    def test_returns_error_message_if_canvas_throws_error(
        self, canvas, client, teacher
    ):
        """
        GIVEN the application encounters an error when reaching Canvas API
        WHEN the get request is sent to the URL
        THEN the a error message is returned in the JSON
        """
        canvas.return_value.get_course.side_effect = Exception()
        resp = client.get("/api/course/1/", headers=token(teacher))
        assert 500 == resp.status_code
        assert isinstance(resp.get_json(), dict)
        assert "message" in resp.get_json()


@pytest.mark.usefixtures("setup_coursemap")
class TestGetAssignments(object):
    """
    FUNCTION    get_assignments
    URL         /api/course/<id>/assignments/
    """

    def test_returns_list_of_assignments_for_teachers_and_tas_without_setup(
        self, client, teacher, ta
    ):
        """
        GIVEN   the assignment settings are NOT set up in the app
        WHEN    the teacher or a TA requests the list of assignments
        THEN    the app returns the list of assignments as JSON
        """
        resp = client.get("/api/course/1/assignments/", headers=token(teacher))
        assert 200 == resp.status_code
        assert isinstance(resp.get_json(), list)
        assert 3 == len(resp.get_json())

        resp = client.get("/api/course/1/assignments/", headers=token(ta))
        assert 200 == resp.status_code
        assert isinstance(resp.get_json(), list)
        assert 3 == len(resp.get_json())

    def test_returns_empty_list_to_students_when_course_is_not_setup(
        self, client, student
    ):
        """
        GIVEN   the teacher has not setup the course in the app
        WHEN    student requests the list of assignments
        THEN    the app returns an empty list as JSON
        """
        resp = client.get("/api/course/1/assignments/", headers=token(student))
        assert 200 == resp.status_code
        assert isinstance(resp.get_json(), list)
        assert 0 == len(resp.get_json())

    @pytest.mark.usefixtures("init_assignments")
    def test_returns_empty_list_to_students_without_pairing_enabled(
        self, client, student
    ):
        """
        GIVEN   the teacher has initialized the course
        WHEN    a student user requests list of assignments
        THEN    the app returns the list of assignments as JSON
        """
        resp = client.get("/api/course/1/assignments/", headers=token(student))
        assert 200 == resp.status_code
        assert isinstance(resp.get_json(), list)
        assert [] == resp.get_json()

    def test_returns_only_pairing_enabled_assignments_to_students(
        self, client, paired_students, init_assignments
    ):
        """
        GIVEN   the teacher has initialized the course
        WHEN    a student requests the list of assignments from the course
        THEN    the app returns only the assignments which meet either of the
                two following conditions:
                - student pairings of any type have been created
                - extra reviews have been enabled
        """
        grader, recipient = paired_students
        resp = client.get("/api/course/1/assignments/", headers=token(grader))
        assert isinstance(resp.get_json(), list)
        assert 1 == len(resp.get_json())

        assignment_2 = init_assignments[1]
        assignment_2.allow_student_pairing = True
        assignment_2.save()
        resp = client.get("/api/course/1/assignments/", headers=token(grader))
        assert 2 == len(resp.get_json())


@pytest.mark.usefixtures("setup_coursemap")
class TestGetAssignment(object):
    """
    FUNCTION    get_assignment
    URL         /api/course/<course_id>/assignment/<assign_id>/
    """

    def test_returns_assignment_to_teacher_and_ta_without_setup(
        self, client, teacher, ta
    ):
        """
        GIVEN   the assignment is not setup in the app
        WHEN    the teacher or a TA request for the assignment
        THEN    the assignment data is returned as JSON
        """
        resp = client.get("/api/course/1/assignment/1/", headers=token(teacher))
        assert 200 == resp.status_code
        assert isinstance(resp.get_json(), dict)
        assert 1 == resp.get_json()["id"]

        resp = client.get("/api/course/1/assignment/1/", headers=token(ta))
        assert 200 == resp.status_code
        assert isinstance(resp.get_json(), dict)
        assert 1 == resp.get_json()["id"]

    def test_returns_error_to_students_when_assignment_is_not_setup(
        self, client, student
    ):
        """
        GIVEN   the assignment is NOT setup in the app
        WHEN    a student requests the assignment
        THEN    an error is returned as JSON with code 404
        """
        resp = client.get("/api/course/1/assignment/1/", headers=token(student))
        assert 404 == resp.status_code
        assert isinstance(resp.get_json(), dict)
        assert "message" in resp.get_json()

    @pytest.mark.usefixtures("init_assignments")
    def test_returns_assignment_to_students_when_assignment_is_setup(
        self, client, student
    ):
        """
        GIVEN   the assignment is setup in the app
        WHEN    a student requests an assignment
        THEN    the assignment details are returned as JSON
        """
        resp = client.get("/api/course/1/assignment/1/", headers=token(student))
        assert 200 == resp.status_code
        assert isinstance(resp.get_json(), dict)
        assert 1 == resp.get_json()["id"]


class TestGetStudents(object):
    """
    FUNCTION    get_students
    URL         /api/course/<id>/students/
    """

    @pytest.mark.usefixtures("setup_coursemap")
    def test_returns_403_if_requested_by_students_after_initialization(
        self, client, student
    ):
        """
        GIVEN   the course initialized
        WHEN    a student sends a GET request to the URL
        THEN    a 403 FORBIDDEN message is sent with message in JSON
        """
        resp = client.get("/api/course/1/students/", headers=token(student))
        assert 403 == resp.status_code
        assert isinstance(resp.get_json(), dict)
        assert "message" in resp.get_json()

    def test_returns_400_if_course_is_not_initialized(self, client, ta, teacher):
        """
        GIVEN   the course is not initialized
        WHEN    the TA asks for the list of students
        THEN    return a 403 error saying the course is not initialized
        """
        resp = client.get("/api/course/1/students/", headers=token(ta))
        assert 400 == resp.status_code
        assert isinstance(resp.get_json(), dict)
        assert "message" in resp.get_json()

        resp = client.get("/api/course/1/students/", headers=token(teacher))
        assert 400 == resp.status_code
        assert isinstance(resp.get_json(), dict)
        assert "message" in resp.get_json()

    @pytest.mark.usefixtures("setup_coursemap")
    def test_returns_list_of_students_to_ta_and_teachers(self, client, ta, teacher):
        """
        GIVEN   the course is initialized by the teacher
        WHEN    a TA or a Teacher requests a list of students
        THEN    return the list of students
        """
        resp = client.get("/api/course/1/students/", headers=token(ta))
        assert 200 == resp.status_code
        assert isinstance(resp.get_json(), list)
        assert len(resp.get_json())

    @pytest.mark.usefixtures("setup_coursemap")
    def test_returns_403_error_for_student_requests(self, client, student):
        """
        GIVEN   the course is initialized by the teacher
        WHEN    a student requests a list of students in the course
        THEN    403 error is returned
        """
        resp = client.get("/api/course/1/students/", headers=token(student))
        assert 403 == resp.status_code
        assert isinstance(resp.get_json(), dict)
        assert "message" in resp.get_json()


@pytest.mark.usefixtures("init_assignments")
class TestGetSubmission(object):
    """
    FUNCTION    get_submission
    URL         /api/course/<id>/assignment/<id>/user/<id>/
    """

    @pytest.mark.usefixtures("setup_coursemap")
    def test_returns_submission_for_self_ta_and_teacher(
        self, client, student, teacher, ta
    ):
        """
        GIVEN   the course has been setup in the application
        WHEN    request for a submission is sent by the submitter, ta or teacher
        THEN    the submission object is returned to the user
        """
        url = "/api/course/1/assignment/1/user/{0}/".format(student.id)

        resp = client.get(url, headers=token(student))
        assert 200 == resp.status_code
        assert isinstance(resp.get_json(), dict)
        assert "workflow_state" in resp.get_json()

        resp = client.get(url, headers=token(teacher))
        assert 200 == resp.status_code
        assert isinstance(resp.get_json(), dict)
        assert "workflow_state" in resp.get_json()

        resp = client.get(url, headers=token(ta))
        assert 200 == resp.status_code
        assert isinstance(resp.get_json(), dict)
        assert "workflow_state" in resp.get_json()

    @pytest.mark.usefixtures("setup_coursemap")
    @patch("peerfeedback.api.views.canvas.get_canvas_client")
    def test_returns_404_if_submission_is_not_submitted(
        self, canvas, client, student, teacher, ta
    ):
        """
        GIVEN   the user has NOT submitted the assignment
        WHEN    the submisssion is requested
        THEN    a 404 error object is returned to the user
        """
        assignment = (
            canvas.return_value.get_course.return_value.get_assignment.return_value
        )
        assignment.get_submission.side_effect = ResourceDoesNotExist("Test")

        url = "/api/course/1/assignment/1/user/{0}/".format(student.id)
        resp = client.get(url, headers=token(teacher))
        assert 404 == resp.status_code
        assert "message" in resp.get_json()

        resp = client.get(url, headers=token(ta))
        assert 404 == resp.status_code
        assert "message" in resp.get_json()

        resp = client.get(url, headers=token(student))
        assert 404 == resp.status_code
        assert "message" in resp.get_json()

    def test_returns_submission_if_requester_is_paired_to_submitter(
        self, client, paired_students
    ):
        """
        GIVEN assignment is submitted and requesting user is paired to submitter
        WHEN    the grader requests the submission
        THEN    the submission object is returned as JSON
        """
        grader, recipient = paired_students
        url = "/api/course/1/assignment/1/user/{0}/".format(recipient.id)
        resp = client.get(url, headers=token(grader))
        assert 200 == resp.status_code
        assert isinstance(resp.get_json(), dict)
        assert "workflow_state" in resp.get_json()

    def test_returns_400_if_the_course_is_not_setup(self, client, student, ta, teacher):
        """
        GIVEN   the course is not setup
        WHEN    a submission is requested by any user
        THEN    an error would be returned
        """
        url = "/api/course/1/assignment/1/user/{0}/".format(student.id)

        resp = client.get(url, headers=token(student))
        assert 400 == resp.status_code

        resp = client.get(url, headers=token(ta))
        assert 400 == resp.status_code

        resp = client.get(url, headers=token(teacher))
        assert 400 == resp.status_code


@pytest.mark.usefixtures("setup_coursemap", "feedback")
class TestSubmissionFeedbacks(object):
    """
    FUNCTION    submission_feedbacks
    URL         /course/<id>/assignment/<id>/user/<id>/feedbacks/
    """

    def test_feedbacks_are_returned_for_teacher_and_ta(
        self, client, student, teacher, ta
    ):
        """
        GIVEN   there are feedback submitted for a submission
        WHEN    a teacher or a TA requests for the feedback
        THEN    the feedbacks are returns as a list in JSON
        """
        url = "/api/course/1/assignment/1/user/{0}/feedbacks/".format(student.id)
        resp = client.get(url, headers=token(teacher))
        assert 200 == resp.status_code
        assert isinstance(resp.get_json(), list)
        assert 2 == len(resp.get_json())

        resp = client.get(url, headers=token(ta))
        assert 200 == resp.status_code
        assert isinstance(resp.get_json(), list)
        assert 2 == len(resp.get_json())

    def test_only_student_feedbacks_are_returned_for_grader(
        self, client, paired_students
    ):
        """
        GIVEN   there is feedback submitted by the grader
        WHEN    the grader or self requests the feedbacks for the submission
        THEN    the feedbacks are returned as list in JSON
        """
        grader, recipient = paired_students
        url = "/api/course/1/assignment/1/user/{0}/feedbacks/".format(recipient.id)
        resp = client.get(url, headers=token(grader))
        assert 200 == resp.status_code
        assert isinstance(resp.get_json(), list)
        assert 1 == len(resp.get_json())
        types = [f["type"] for f in resp.get_json()]
        assert "TA" not in types

    def test_all_feedbacks_are_returned_for_recipient(self, client, paired_students):
        """
        GIVEN   there is feedback submitted by the grader
        WHEN    the grader or self requests the feedbacks for the submission
        THEN    the feedbacks are returned as list in JSON
        """
        grader, recipient = paired_students
        url = "/api/course/1/assignment/1/user/{0}/feedbacks/".format(recipient.id)
        resp = client.get(url, headers=token(recipient))
        assert 200 == resp.status_code
        assert isinstance(resp.get_json(), list)
        assert 2 == len(resp.get_json())

    def test_returns_403_forbidden_for_unpaired_students(
        self, client, paired_students, random_student
    ):
        """
        GIVEN   the feedback is submitted by the graders
        WHEN    a student who is not paired to the recipient requests the feedbacks
        THEN    an error message with 403 Forbidden is returned
        """
        grader, recipient = paired_students
        url = "/api/course/1/assignment/1/user/{0}/feedbacks/".format(recipient.id)
        resp = client.get(url, headers=token(random_student))
        assert 403 == resp.status_code


@pytest.mark.usefixtures("users", "setup_coursemap")
class TestGetPeers(object):
    """
    FUNCTION    get_peers
    URL         /api/course/<id>/assignment/<id>/peers/
    """

    def test_returns_a_list_of_users(self, client, student):
        """
        GIVEN   the course is initialized
        WHEN    a student requests for peers
        THEN    the other students enrolled in the group are returned as a list
        """
        resp = client.get("/api/course/1/assignment/1/peers/", headers=token(student))
        assert 200 == resp.status_code
        assert isinstance(resp.get_json(), list)
        assert 72 == len(resp.get_json())

    def test_returned_list_does_not_contain_self(self, client, student):
        """
        GIVEN   the course is initialized
        WHEN    a student request for peers
        THEN    the returned list should not containt the user itself
        """
        resp = client.get("/api/course/1/assignment/1/peers/", headers=token(student))
        assert 200 == resp.status_code
        assert student.id not in [s["id"] for s in resp.get_json()]

    @patch("peerfeedback.api.views.all.get_course_teacher")
    def test_returns_error_if_the_teacher_is_not_found(
        self, course_teacher, client, student
    ):
        """
        GIVEN   the course is not initialized
        WHEN    a user requests the peers
        THEN    an error is returned with the message
        """
        course_teacher.return_value = None
        resp = client.get("/api/course/1/assignment/1/peers/", headers=token(student))
        assert 400 == resp.status_code
        assert "message" in resp.get_json()

    def test_returned_list_does_not_contained_already_paired_peers(
        self, client, paired_students
    ):
        """
        GIVEN   a student is already paired to another student
        WHEN    the student requests for peers
        THEN    the returned list should not contain the paired student
        """
        grader, recipient = paired_students
        resp = client.get("/api/course/1/assignment/1/peers/", headers=token(grader))
        assert 200 == resp.status_code
        assert 71 == len(resp.get_json())
        assert recipient.id not in [s["id"] for s in resp.get_json()]

    @pytest.mark.usefixtures("extra_requests")
    def test_returned_peers_have_extra_review_requests_flagged(self, client, student):
        """
        GIVEN   some students have requested for extra feedback
        WHEN    a student requests list of peers
        THEN    the returned list contains extra request flag set to true
        """
        resp = client.get("/api/course/1/assignment/1/peers/", headers=token(student))
        assert 200 == resp.status_code
        peers = resp.get_json()
        user_10 = next((p for p in peers if p["id"] == 10), None)
        assert user_10["extra_requested"]
        user_11 = next((p for p in peers if p["id"] == 11), None)
        assert user_11["extra_requested"]


class TestClearNotifications(object):
    """
    METHOD  clear_notifications
    URL     /api/notifications/clear/
    """

    def test_notifications_are_cleared_for_the_user(self, client, student):
        """
        GIVEN   there are some unread notifications for a user in the DB
        WHEN    a post request is sent to the URL
        THEN    all the notifications of that user are marked read
        """
        for i in range(8):
            note = Notification.create(recipient_id=student.id)
            assert not note.read

        resp = client.post("/api/notifications/clear/", headers=token(student))
        assert 200 == resp.status_code
        assert "OK" == resp.data.decode()

        for n in Notification.query.all():
            assert n.read
            n.delete()

    def test_notification_does_not_affect_other_users(self, client, student, teacher):
        """
        GIVEN   there are some unread notifications for a user in the DB
        WHEN    a post request is sent to the URL by one user
        THEN    notifications of other users shouldn't be disturbed
        """
        for i in range(5):
            note = Notification.create(recipient_id=teacher.id)
            assert not note.read

        resp = client.post("/api/notifications/clear/", headers=token(student))
        assert 200 == resp.status_code
        assert "OK" == resp.data.decode()

        for n in Notification.query.all():
            assert not n.read
            n.delete()


class TestGetExtraFeedbackCount(object):
    """
    METHOD  get_count_of_extra_feedback_given
    URL     /api/course/<id>/assignment/<id>/extras_given/
    """

    @staticmethod
    def create_pair(grader, n):
        recipient = User.query.filter_by(email=f"student{n:04}@example.edu").first()
        Pairing.create(
            type=Pairing.STUDENT,
            course_id=10,
            assignment_id=99,
            grader=grader,
            recipient=recipient,
            creator=grader,
        ).save()

    def test_the_returned_count_matches_the_pairs_in_db(self, client, student):
        """
        GIVEN   there are n pairs created by the student
        WHEN    the count of the extra feedback given are requested
        THEN    n is returned
        """
        for i in range(8):
            response = client.get(
                "/api/course/10/assignment/99/extras_given/", headers=token(student)
            )
            assert i == int(response.data)
            self.create_pair(student, i + 2)
        Pairing.query.filter_by(
            course_id=10, assignment_id=99, grader=student, creator=student
        ).delete()
