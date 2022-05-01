import re

import pytest
import json
from unittest.mock import patch

from peerfeedback.api import errors
from tests.factories import token


@pytest.mark.usefixtures("setup_coursemap")
class TestManualPairing(object):
    """
    FUNCTION    manual_pairing
    URL         /pairing/manual/
    """

    def test_post_checks_for_required_params(self, client):
        """
        GIVEN   the app is running
        WHEN    a post request is made without any of the required params
        THEN    a 400 error is returned
        """
        data = dict(course_id=1, grader=1, recipient=2)
        res = client.post(
            "/api/pairing/manual/",
            data=json.dumps(data),
            content_type="application/json",
        )
        assert 400 == res.status_code
        assert errors.MISSING_PARAMS == res.get_json()["message"]
        assert ["assignment_id"] == res.get_json()["missing"]

    def test_post_only_allows_teachers(self, client, student):
        """
        GIVEN   the course is setup
        WHEN    a post request is made by a student
        THEN    a 403 error is returned
        """
        data = dict(course_id=1, assignment_id=2, grader=1, recipient=2)
        res = client.post(
            "/api/pairing/manual/",
            data=json.dumps(data),
            headers=token(student),
            content_type="application/json",
        )
        assert 403 == res.status_code
        assert errors.NOT_AUTHORISED == res.get_json()["message"]

    def test_post_returns_400_for_pairing_with_self(self, client, teacher):
        """
        GIVEN   the course is setup
        WHEN    a post request is made with the same id for both grader and recipient
        THEN    a 400 is returned
        """
        data = dict(course_id=1, assignment_id=2, grader=1, recipient=1)
        res = client.post(
            "/api/pairing/manual/",
            data=json.dumps(data),
            headers=token(teacher),
            content_type="application/json",
        )
        assert 400 == res.status_code
        assert errors.GRADER_RECIPIENT_SAME == res.get_json()["message"]


@pytest.mark.usefixtures("setup_coursemap")
class TestCSVPairing(object):
    """
    FUNCTION    csv_pairing
    URL         /pairing/csv/
    """

    def test_only_teachers_can_do_csv_pairing(self, client, student):
        """
        GIVEN   the course is setup
        WHEN    a csv pairing post request is made by a student
        THEN    a 403 is returned
        """
        data = dict(
            course_id=1, assignment_id=1, pairs=[], allowMissing=0, graderType=""
        )
        res = client.post(
            "/api/pairing/csv/",
            data=json.dumps(data),
            headers=token(student),
            content_type="application/json",
        )
        assert 403 == res.status_code

    def test_returns_400_for_missing_params(self, client, teacher):
        """
        GIVEN   the course is setup
        WHEN    a csv pairing post request with missing parameters
        THEN    a 400 is returned with the missing parameters
        """
        data = dict(course_id=1, assignment_id=1, pairs=[])
        res = client.post(
            "/api/pairing/csv/",
            data=json.dumps(data),
            headers=token(teacher),
            content_type="application/json",
        )
        assert 400 == res.status_code
        assert errors.MISSING_PARAMS == res.get_json()["message"]
        assert "missing" in res.get_json()

    @patch("peerfeedback.api.views.pairing.pair_using_csv")
    def test_job_is_called_when_all_data_are_passed(self, mock_job, client, teacher):
        """
        GIVEN   the course is setup
        WHEN    a csv pairing post request with all the params by a teacher
        THEN    the csv pairing job is initiated
        """
        mock_job.queue.return_value.id = "dummy-id"
        data = dict(
            course_id=1,
            assignment_id=1,
            pairs=[],
            allowMissing=True,
            graderType="student",
        )
        res = client.post(
            "/api/pairing/csv/",
            data=json.dumps(data),
            headers=token(teacher),
            content_type="application/json",
        )
        assert res.status_code == 200
        mock_job.queue.assert_called_once()


@pytest.mark.usefixtures("setup_coursemap")
class TestAutomaticPairing(object):
    """
    FUNCTION    automatic_pairing
    URL         /pairing/automatic/
    """

    def test_returns_400_for_missing_params(self, client, teacher):
        """
        GIVEN   the app is setup and course initialized
        WHEN    an automatic pairing request is made with missing params
        THEN    a 400 bad request is returned
        """
        data = dict(course_id=1, assignment_id=1)
        res = client.post(
            "/api/pairing/automatic/",
            data=json.dumps(data),
            content_type="application/json",
        )
        assert res.status_code == 400
        assert errors.MISSING_PARAMS == res.get_json()["message"]

    def test_returns_403_for_students(self, client, student):
        """
        GIVEN   the app is setup and course initialized
        WHEN    an automatic pairing request is made by a student
        THEN    a 403 forbidden request is returned
        """
        data = dict(
            course_id=1, assignment_id=1, reviewRounds=5, excludeDefaulters=True,
            excludedStudents=""
        )
        res = client.post(
            "/api/pairing/automatic/",
            data=json.dumps(data),
            headers=token(student),
            content_type="application/json",
        )
        assert res.status_code == 403

    @patch("peerfeedback.api.views.pairing.pair_automatically")
    def test_automatic_pairing_job_is_started(self, mock_job, client, teacher):
        """
        GIVEN   the app is setup and course initialized
        WHEN    an automatic pairing request is made with right params
        THEN    the background job for the pairing is started and job id returned
        """
        mock_job.queue.return_value.id = "job-id"
        data = dict(
            course_id=1, assignment_id=1, reviewRounds=5, excludeDefaulters=True,
            excludedStudents=""
        )
        res = client.post(
            "/api/pairing/automatic/",
            data=json.dumps(data),
            headers=token(teacher),
            content_type="application/json",
        )
        assert res.status_code == 200
        assert "job-id" == res.get_json()["id"]


@pytest.mark.usefixtures("setup_coursemap")
class TestTAPairing(object):
    """
    FUNCTION    ta_pairing
    URL         /pairing/ta/
    """

    def test_returns_400_for_missing_params(self, client, teacher):
        """
        GIVEN   the app is setup and course initialized
        WHEN    a TA pairing request is made with missing params
        THEN    a 400 bad request is returned
        """
        data = dict(course_id=1, assignment_id=1)
        res = client.post(
            "/api/pairing/ta/", data=json.dumps(data), content_type="application/json"
        )
        assert res.status_code == 400
        assert errors.MISSING_PARAMS == res.get_json()["message"]

    def test_returns_403_for_students(self, client, student):
        """
        GIVEN   the app is setup and course initialized
        WHEN    a TA pairing request is made by a student
        THEN    a 403 forbidden request is returned
        """
        data = dict(course_id=1, assignment_id=1, allocation=[])
        res = client.post(
            "/api/pairing/ta/",
            data=json.dumps(data),
            headers=token(student),
            content_type="application/json",
        )
        assert res.status_code == 403

    @patch("peerfeedback.api.views.pairing.allocate_students_to_tas")
    def test_ta_allocation_job_is_started(self, mock_job, client, teacher):
        """
        GIVEN   the app is setup and course initialized
        WHEN    an automatic pairing request is made with right params
        THEN    the background job for the pairing is started and job id returned
        """
        mock_job.queue.return_value.id = "job-id"
        data = dict(course_id=1, assignment_id=1, allocation=[])
        res = client.post(
            "/api/pairing/ta/",
            data=json.dumps(data),
            headers=token(teacher),
            content_type="application/json",
        )
        assert res.status_code == 200
        assert "job-id" == res.get_json()["id"]


@pytest.mark.usefixtures("setup_coursemap", "pairings")
class TestGetPairings(object):
    """
    METHOD  get_pairings
    URL     /api/course/<id>/assignment/<id>/pairs/
    """

    def test_returns_pairs_for_first_10_students_by_default(self, client, teacher, ta):
        """
        GIVEN   there are pairings in the database
        WHEN    a request for list of pairs is made by teacher or ta
        THEN    pairs of only 10 students are returned by default
        """
        resp = client.get("/api/course/1/assignment/1/pairs/", headers=token(teacher))
        assert 200 == resp.status_code
        assert 10 == len(resp.get_json()["pairs"])
        assert 10 == resp.get_json()["per_page"]

        resp = client.get("/api/course/1/assignment/1/pairs/", headers=token(ta))
        assert 200 == resp.status_code
        assert 10 == len(resp.get_json()["pairs"])

    def test_returns_pairs_of_student_set_by_limit_argument(self, client, teacher):
        """
        GIVEN   pairing has been completed for a course
        WHEN    the get pairs requests is made with the limit parameter
        THEN    the pairs of "limit" number of students are returned
        """
        resp = client.get(
            "/api/course/1/assignment/1/pairs/?per_page=25", headers=token(teacher)
        )
        assert 25 == len(resp.get_json()["pairs"])

    def test_results_are_returned_page_wise(self, client, teacher):
        """
        GIVEN   there are pairings in for a course
        WHEN    a request for the pairs is made with the page argument
        THEN    pairs of only that page of students is returned
        """
        resp = client.get(
            "/api/course/1/assignment/1/pairs/?page=1", headers=token(teacher)
        )
        assert 200 == resp.status_code
        assert 10 == len(resp.get_json()["pairs"])

        resp2 = client.get(
            "/api/course/1/assignment/1/pairs/?page=2", headers=token(teacher)
        )
        assert 200 == resp2.status_code
        assert 10 == len(resp2.get_json()["pairs"])

        pids_1 = set(p["grader"]["id"] for p in resp.get_json()["pairs"])
        pids_2 = set(p["grader"]["id"] for p in resp2.get_json()["pairs"])

        assert list(pids_1 & pids_2) == []

    def test_response_contains_pagination_markers(self, client, teacher):
        """
        GIVEN   there are pairings for a course
        WHEN    a request is sent by the teacher for a list of pairs
        THEN    the response contains the markers for pagination
        """
        resp = client.get("/api/course/1/assignment/1/pairs/", headers=token(teacher))
        data = resp.get_json()
        assert "page" in data
        assert "next" in data
        assert "?page=2" in data["next"]
        assert "per_page" in data

    def test_response_pagination_marker_does_not_exist_after_last_page(
        self, client, teacher
    ):
        """
        GIVEN   there are pairings for a course
        WHEN    a request is made for the last page of the list of pairs
        THEN    the response doesn't include the next pagination marker
        """
        # Note: there are 73 students, so 8 pages of results with 10 per page
        resp = client.get(
            "/api/course/1/assignment/1/pairs/?page=7", headers=token(teacher)
        )
        assert "page" in resp.get_json()
        assert "next" in resp.get_json()
        assert "?page=8" in resp.get_json()["next"]

        resp = client.get(
            "/api/course/1/assignment/1/pairs/?page=8", headers=token(teacher)
        )
        assert "page" in resp.get_json()
        assert "next" not in resp.get_json()
        assert 3 == len(resp.get_json()["pairs"])

    def test_returns_error_when_student_makes_the_request(self, client, student):
        """
        GIVEN   there are pairings for a course
        WHEN    the get request is made by a student
        THEN    an 403 error is returned
        """
        resp = client.get("/api/course/1/assignment/1/pairs/", headers=token(student))
        assert 403 == resp.status_code
        assert "message" in resp.get_json()

    def test_when_page_argument_is_beyond_limit_empty_list_is_returned(
        self, client, teacher
    ):
        """
        GIVEN   there are pairs for a course
        WHEN    the request for an page that is beyond the possible value is made
        THEN    a 400 bad request error is returned with a message
        """
        resp = client.get(
            "/api/course/1/assignment/1/pairs/?page=999", headers=token(teacher)
        )
        assert 200 == resp.status_code
        assert [] == resp.get_json()["pairs"]


@pytest.mark.usefixtures("setup_coursemap", "pairings")
class TestSearchPairings(object):
    """
    METHOD  search_pairs
    URL     /api/pairs/search
    """

    def test_returns_list_of_pairs_for_teacher_or_ta(self, client, teacher, ta):
        """
        GIVEN   pairing has been done for a course
        WHEN    a search query is sent for the pairs by a teacher or a ta
        THEN    the list of pairs are returned
        """
        resp = client.get(
            "/api/course/1/assignment/1/pairs/search?grader=Student 70",
            headers=token(teacher),
        )
        assert 200 == resp.status_code
        data = resp.get_json()
        assert isinstance(data, list)
        assert 1 == len(data)

        resp = client.get(
            "/api/course/1/assignment/1/pairs/search?recipient=Student 70",
            headers=token(teacher),
        )
        data = resp.get_json()
        assert 1 == len(data)

    def test_returns_error_for_students(self, client, student):
        """
        GIVEN   pairing has been done for a course
        WHEN    a student tries to search for the pairs
        THEN    an error message is returned to the student
        """
        resp = client.get(
            "/api/course/1/assignment/1/pairs/search?grader=student",
            headers=token(student),
        )
        assert 403 == resp.status_code
        assert "message" in resp.get_json()

    def test_redirect_to_get_pairings_if_search_params_are_missing(
        self, client, teacher
    ):
        """
        GIVEN   pairing has been done for the course
        WHEN    a search request is sent without any search params
        THEN    the user is redirected to the get_pairings page so all the pairs
                of the assignment are returned
        """
        resp = client.get(
            "/api/course/1/assignment/1/pairs/search", headers=token(teacher)
        )
        assert 302 == resp.status_code
        assert re.match(
            ".*/api/course/1/assignment/1/pairs/$", resp.headers["location"]
        )


@pytest.mark.usefixtures("setup_coursemap", "pairing", "task")
class TestGetMyPairings(object):
    """
    METHOD  get_my_pairings
    URL     /api/course/<id>/assignment/<id>/pairs/mine/
    """

    def test_returns_pairs_of_the_requesting_student(self, client, student):
        """
        GIVEN   pairing has been done for an assignment
        WHEN    a student requests the pairs he is a part of
        THEN    a list of pairs is returned
        """
        resp = client.get(
            "/api/course/1/assignment/1/pairs/mine/", headers=token(student)
        )
        assert 200 == resp.status_code
        assert 1 == len(resp.get_json())
