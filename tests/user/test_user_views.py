# -*- coding: utf-8 -*-
"""User Blueprint unit tests."""
import os
import json
import pytest

from unittest.mock import patch, Mock

from peerfeedback.models import User, JWTToken, UserSettings

CANVAS_MOCK_RESPONSE = {
    "user": {"id": 10, "name": "Test User", "email": "user@test.com"},
    "access_token": "dummy_access_token",
    "refresh_token": "dummy_refresh_token",
}

MOCK_USER_PROFILE = {
    "name": "Test user",
    "id": 32,
    "login_id": "testuser",
    "primary_email": "user@test.edu",
}


class TestLoginView(object):
    def test_redirects_to_canvas_login_page(self, client):
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
        response = client.get("/users/login/")
        assert response.status_code == 302


@patch("peerfeedback.user.views.Canvas")
@patch("peerfeedback.user.views.canvas_oauth")
class TestOAuthAuthorizedView(object):
    """
    FUNCTION    oauth_authorized()
    URL         /users/oauth-authorized/
    """

    def test_adds_new_user_with_settings_if_not_found(
        self, mock_canvas, mock_canvas_api, client, db
    ):
        """
        GIVEN   the user is not present in the database
        WHEN    the user oauth authorizes
        THEN    a new user with settings is added to the database
        """
        mock_canvas.authorize_access_token.return_value = CANVAS_MOCK_RESPONSE
        mock_canvas_api.return_value.get_user.return_value.get_profile.return_value = (
            MOCK_USER_PROFILE
        )
        assert 0 == db.session.query(User).count()
        assert 0 == db.session.query(UserSettings).count()
        client.get("/users/oauth-authorized/")
        assert 1 == db.session.query(User).count()
        assert 1 == db.session.query(UserSettings).count()
        User.query.delete()

    def test_redirects_to_app_with_tokens_as_cookies(
        self, mock_canvas, mock_canvas_api, db, client
    ):
        """
        GIVEN   the user is not present in the database
        WHEN    the user oauth authorizes and the user is added
        THEN    a 302 redirect is returned with tokens in the cookies
        """
        mock_canvas.authorize_access_token.return_value = CANVAS_MOCK_RESPONSE
        mock_canvas_api.return_value.get_user.return_value.get_profile.return_value = (
            MOCK_USER_PROFILE
        )
        response = client.get("/users/oauth-authorized/")
        assert 302 == response.status_code
        assert "access_token" in str(response.headers)
        assert "refresh_token" in str(response.headers)
        assert 1 == db.session.query(User).count()
        assert 1 == db.session.query(UserSettings).count()
        User.query.delete()

    @patch("peerfeedback.user.views.requests.delete")
    def test_updates_access_token_for_existing_users(
        self, md, mock_canvas, mo_api, client, db, student
    ):
        """
        GIVEN   an existing user completes oauth successfully
        WHEN    the user is redirected to the this URL
        THEN    a new canvas access token is stored for the user
        """
        mock_resp = CANVAS_MOCK_RESPONSE
        mock_resp["user"]["id"] = student.canvas_id
        mock_canvas.authorize_access_token.return_value = mock_resp
        client.get("/users/oauth-authorized/")
        assert "dummy_access_token" == student.canvas_access_token

    def test_error_when_no_user_not_returned_by_canvas(self, mc, mc_api, client):
        """
        GIVEN   the user is doing the oauth login
        WHEN    the does not authorize the oauth request
        THEN    an error message is returned
        """
        mc.authorize_access_token.return_value = None
        response = client.get("/users/oauth-authorized/")
        assert "Login failed !!!" in response.data.decode()

    def test_error_when_authorization_fails(self, mc, mc_api, client):
        """
        GIVEN   the user is doing the oauth login
        WHEN    there is an OAuth exception which stops the authorization process
        THEN    an error message is returned
        """
        mc.authorize_access_token.side_effect = Mock(
            side_effect=Exception("invalid response")
        )
        response = client.get("/users/oauth-authorized/")
        assert "Login failed !!!" in response.data.decode()

    @patch("peerfeedback.user.views.requests.delete")
    def test_adds_jwt_token_to_db(self, md, mc, mc_api, client, db):
        """
        GIVEN   an existing user completes oauth successfully
        WHEN    the user is redirected to the this URL
        THEN    two new JWT tokens are generated and stored in the DB
        """
        mc.authorize_access_token.return_value = CANVAS_MOCK_RESPONSE
        mc_api.return_value.get_user.return_value.get_profile.return_value = (
            MOCK_USER_PROFILE
        )

        JWTToken.query.delete()
        assert 0 == db.session.query(JWTToken).count()
        client.get("/users/oauth-authorized/")
        # login adds 1 access token and 1 refresh token to DB
        assert 2 == db.session.query(JWTToken).count()
