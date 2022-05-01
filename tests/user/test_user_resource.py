import pytest
import json

from flask_restful import marshal

from peerfeedback.user.resource import user_fields
from peerfeedback.models import UserSettings

from tests.factories import token


class TestUserProfile(object):
    """
    URL         /users/profile/
    """

    def test_get_returns_user_object(self, client, student):
        """
        GIVEN   there exists a user in the database
        WHEN    a get request is sent to fetch his profile
        THEN    the user profile is returned as JSON
        """
        expected = marshal(student, user_fields)
        response = client.get("/users/profile/", headers=token(student))
        assert 200 == response.status_code
        data = response.get_json()
        assert expected == data

    def test_get_returns_401_for_non_existing_users(self, client):
        """
        GIVEN   there doesn't exist a user
        WHEN    a get request for profile is made without the jwt identifier
        THEN    an error is returned
        """
        response = client.get("/users/profile/")
        assert 401 == response.status_code

    def test_put_updates_the_display_name(self, users, client):
        """
        GIVEN   there exists a user in the DB
        WHEN    the user makes a put request with updated details
        THEN    the data is updated in the database
        """
        user = users[0]
        assert "New Name" != user.name
        response = client.put(
            "/users/profile/",
            data='{"name": "New Name"}',
            content_type="application/json",
            headers=token(user),
        )
        assert 200 == response.status_code
        assert "New Name" == user.name

        assert "new@example.com" != user.email
        response = client.put(
            "/users/profile/",
            data='{"email": "new@example.com"}',
            content_type="application/json",
            headers=token(user),
        )
        assert 200 == response.status_code
        assert "new@example.com" == user.email


@pytest.fixture
def user_settings(student):
    settings = UserSettings.create(user_id=student.id)
    yield settings
    settings.delete()


class TestUserSettings(object):
    """
    URL   /users/settings/
    """

    @pytest.mark.usefixtures("user_settings")
    def test_get_returns_current_user_settings(self, client, student):
        """
        GIVEN   there exists a user and his settings
        WHEN    a get request is made
        THEN    the user's settings is returned as JSON
        """
        response = client.get("/users/settings/", headers=token(student))
        assert 200 == response.status_code
        data = response.get_json()
        assert isinstance(data, dict)
        assert "feedback_emails" in data
        assert "comment_emails" in data
        assert "discussion_emails" in data

    def test_put_updates_user_settings(self, client, student, user_settings):
        """
        GIVEN   the user and his settings exist
        WHEN    a put request is made to update the settings
        THEN    the data is updated in the database
        """
        # test with just one value
        assert user_settings.feedback_emails is True
        data = dict(feedback_emails=False)
        response = client.put(
            "/users/settings/",
            data=json.dumps(data),
            content_type="application/json",
            headers=token(student),
        )
        assert 200 == response.status_code
        response_dict = json.loads(response.data.decode())
        assert response_dict["feedback_emails"] is False

        # test with multiple values
        assert user_settings.comment_emails is True
        assert user_settings.discussion_emails is True
        data = dict(comment_emails=False, discussion_emails=False)
        response = client.put(
            "/users/settings/",
            data=json.dumps(data),
            content_type="application/json",
            headers=token(student),
        )
        assert 200 == response.status_code
        assert user_settings.comment_emails is False
        assert user_settings.discussion_emails is False

    def test_get_creates_settings_if_a_user_doesnot_have_settings(
        self, db, client, student
    ):
        """
        GIVEN   there exists a user without any settings object
        WHEN    the user requests for personal settings
        THEN    a new settings object is created
        """
        assert 0 == db.session.query(UserSettings).count()
        response = client.get("/users/settings/", headers=token(student))
        assert 200 == response.status_code
        settings = UserSettings.query.get(response.get_json()["id"])
        assert settings
        settings.delete()

    def test_put_returns_404_for_non_existing_id(self, client, student):
        """
        GIVEN   there doesn't exist a settings object for the user
        WHEN    the user sends a PUT request to update the settings
        THEN    a 404 error is returned
        """
        response = client.put("/users/settings/", data={}, headers=token(student))
        assert 404 == response.status_code

    def test_post_creates_user_settings_if_does_not_exist(self, db, client, teacher):
        """
        GIVEN   there isn't a settings for the user
        WHEN    a post request is sent by the user
        THEN    a new settings object is created
        """
        assert 0 == db.session.query(UserSettings).count()
        response = client.post("/users/settings/", headers=token(teacher))
        assert 201 == response.status_code
        settings = UserSettings.query.get(response.get_json()["id"])
        assert settings
        settings.delete()

    def test_post_throws_409_if_settings_already_exists(
        self, client, student, user_settings
    ):
        """
        GIVEN   there exists a settings object for the user
        WHEN    a post request is made by the user to create settings
        THEN    a 409 conflict error is returned
        """
        assert 1 == len(UserSettings.query.all())
        response = client.post("/users/settings/", headers=token(student))
        assert 409 == response.status_code
        assert 1 == len(UserSettings.query.all())
