from unittest.mock import patch


class TestLoginView(object):
    def test_get_returns_admin_login_form(self, client):
        res = client.get("/admin/login/")
        assert "admin-login-form" in str(res.data)

    def test_post_returns_401_for_invalid_user_pass(self, client):
        data = {"username": "user", "password": "pass"}
        res = client.post("/admin/login/", data=data)
        assert res.status_code == 401

    @patch("os.environ.get")
    def test_post_compares_password_with__envvar_for_admin_user(self, mock_get, client):
        mock_get.return_value = "mypass"
        data = {"username": "admin", "password": "pass"}
        res = client.post("/admin/login/", data=data)
        assert res.status_code == 401
        mock_get.assert_called_once()

    @patch("os.environ.get")
    def test_post_returns_message_when_admin_user_is_not_found(self, mock_get, client):
        mock_get.return_value = "mypass"
        data = {"username": "admin", "password": "mypass"}
        res = client.post("/admin/login/", data=data)
        assert res.status_code == 200
        assert "Admin User not present" in str(res.data)
