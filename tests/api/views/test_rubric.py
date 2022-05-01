import json

import pytest

from peerfeedback.models import Rubric, RubricCriteria
from tests.factories import token


@pytest.fixture
def rubrics(db, teacher, ta):
    r1 = Rubric.create(name="Test Rurbic 1", owner_id=teacher.id)
    r2 = Rubric.create(name="Test Rurbic 2", owner_id=teacher.id)
    r3 = Rubric.create(name="Test Rurbic 3", owner_id=ta.id)
    r4 = Rubric.create(name="Test Rubric 4", owner_id=ta.id, public=False)
    r5 = Rubric.create(name="Test Rubric 5", owner_id=ta.id, public=False)
    yield [r1, r2, r3, r4, r5]
    r1.delete()
    r2.delete()
    r3.delete()
    r4.delete()
    r5.delete()


class TestGetRubrics(object):
    """
    FUNCTION  get_rubrics
    URL       /api/rubrics/
    """

    def test_returns_only_public_rubrics_to_non_owners(self, client, student, rubrics):
        """
        GIVEN   some rubrics are saved as public
        WHEN    a user requests rubrics
        THEN    all the public rubrics are returned as JSON
        """
        resp = client.get("/api/rubrics/", headers=token(student))
        assert 200 == resp.status_code
        response_json = resp.get_json()
        assert isinstance(response_json, list)
        assert 3 == len(response_json)

    def test_returns_owned_and_public_rubrics(self, client, teacher, ta, rubrics):
        """
        GIVEN   some rubrics are saved as public and others not
        WHEN    a user who owns rubrics requests for rubrics
        THEN    a list of all rubrics he owns and all other public rubrics are returned
        """
        resp = client.get("/api/rubrics/", headers=token(teacher))
        assert 200 == resp.status_code
        response_json = resp.get_json()
        assert isinstance(response_json, list)
        assert 3 == len(response_json)

        resp = client.get("/api/rubrics/", headers=token(ta))
        assert 200 == resp.status_code
        response_json = resp.get_json()
        assert isinstance(response_json, list)
        assert 5 == len(response_json)


@pytest.mark.usefixtures("setup_coursemap")
class TestCreateRubric(object):
    """
    FUNCTION    create_rubric
    URL         /api/rubric/
    """

    def test_returns_403_for_students(self, client, student):
        """
        GIVEN the user is enrolled only as a student in the app
        WHEN  the user sends a POST request to create rubric
        THEN  a 403 forbidden error message is returned
        """
        data = {"name": "Test Rubric", "criterions": []}
        resp = client.post(
            "/api/rubric/",
            data=json.dumps(data),
            headers=token(student),
            content_type="application/json",
        )
        assert 403 == resp.status_code
        assert "message" in resp.get_json()
        rubrics = Rubric.query.all()
        assert len(rubrics) == 0

    def test_teachers_and_tas_are_allowed_to_create_rubrics(self, client, teacher, ta):
        """
        GIVEN   the user is either a teacher or a ta
        WHEN    a request to create a rubric is sent
        THEN    the rubric is created
        """
        data = {"name": "Test Rubric", "criterions": []}
        resp = client.post(
            "/api/rubric/",
            data=json.dumps(data),
            headers=token(teacher),
            content_type="application/json",
        )
        assert 201 == resp.status_code
        assert 1 == len(Rubric.query.all())

        data = {"name": "Test Rubric", "criterions": []}
        resp = client.post(
            "/api/rubric/",
            data=json.dumps(data),
            headers=token(ta),
            content_type="application/json",
        )
        assert 201 == resp.status_code
        assert 2 == len(Rubric.query.all())

        for rubric in Rubric.query.all():
            rubric.delete()

    def test_returns_if_rubric_name_is_missing(self, client, teacher):
        """
        GIVEN  the user is a teacher or a ta
        WHEN   the request to create a rubric is sent without a rubric name
        THEN   an error is returned with message
        """
        data = {"name": ""}
        resp = client.post(
            "/api/rubric/",
            data=json.dumps(data),
            headers=token(teacher),
            content_type="application/json",
        )
        assert 400 == resp.status_code
        assert "message" in resp.get_json()

    def test_rubric_and_its_criterions_are_saved(self, client, teacher, ta):
        """
        GIVEN   the user is allowed to create rubrics
        WHEN    the rubric data is sent a JSON to the endpoint
        THEN    data is stored as Rubric and RubricCriteria objects
        """
        data = {
            "name": "Test Rubric",
            "description": "Rubric description",
            "criterions": [
                {
                    "name": "Criteria 1",
                    "description": "Crit 1 Desc",
                    "levels": [
                        {"position": 0, "text": "dummy", "points": 5},
                        {"position": 1, "text": "dummy", "points": 10},
                        {"position": 2, "text": "dummy", "points": 15},
                    ],
                },
                {
                    "name": "Criteria 2",
                    "description": "Crit 2 desc",
                    "levels": [
                        {"position": 0, "text": "dummy", "points": 3},
                        {"position": 1, "text": "dummy", "points": 6},
                    ],
                },
            ],
        }
        resp = client.post(
            "/api/rubric/",
            data=json.dumps(data),
            headers=token(teacher),
            content_type="application/json",
        )
        assert 201 == resp.status_code
        assert 1 == len(Rubric.query.all())
        assert 2 == len(RubricCriteria.query.all())

        resp = client.post(
            "/api/rubric/",
            data=json.dumps(data),
            headers=token(ta),
            content_type="application/json",
        )
        assert 201 == resp.status_code
        assert 2 == len(Rubric.query.all())
        assert 4 == len(RubricCriteria.query.all())


class TestGetRubric(object):
    """
    FUNCTION    get_rubric
    URL         /api/rubric/<id>/
    """

    def test_returns_rubric_with_criterions(self, client, student, rubric):
        """
        GIVEN   rubric is present in the database with criterions
        WHEN    the rubric is requested with the ID
        THEN    the rubric and all the criteria are returned as JSON
        """
        url = "/api/rubric/{0}/".format(rubric.id)
        resp = client.get(url, headers=token(student))
        assert 200 == resp.status_code
        data = resp.get_json()
        assert isinstance(data, dict)
        assert 2 == len(data["criterions"])

    def test_returns_404_if_the_rubric_doesnt_exist(self, client, student):
        """
        GIVEN   there is no rubric with the given id
        WHEN    a get request is sent with a non existent rubric id
        THEN    a 404 error is returned
        """
        resp = client.get("/api/rubric/99/", headers=token(student))
        assert 404 == resp.status_code
