# -*- coding: utf-8 -*-
import pytest

from flask_jwt_extended import create_access_token, decode_token

from peerfeedback.exceptions import TokenNotFound
from peerfeedback.models import JWTToken
from peerfeedback.user.jwt_helpers import (
    add_token_to_database,
    revoke_token,
    is_token_revoked,
    _epoch_utc_to_datetime,
)


@pytest.fixture
def token(db):
    token = create_access_token(identity={"username": "testuser"}, fresh=True)
    decoded = decode_token(token)
    token_obj = JWTToken.create(
        jti=decoded["jti"],
        token_type=decoded["type"],
        user_identity=decoded["identity"]["username"],
        expires=_epoch_utc_to_datetime(decoded["exp"]),
        revoked=False,
    )
    yield token
    token_obj.delete()


class TestAddTokenToDB(object):
    """
    FUNCTION    add_token_to_database(encoded_token, identity_claim)
    """

    def test_adds_a_new_token(self, db):
        """
        GIVEN   the db is setup
        WHEN    the function is called with a encoded token
        THEN    the token's params are decoded and stored in the DB
        """
        assert 0 == len(db.session.query(JWTToken).all())
        token = create_access_token(identity={"username": "testuser"}, fresh=True)
        add_token_to_database(token, "identity")
        assert 1 == len(db.session.query(JWTToken).all())


class TestRevokeToken(object):
    """
    FUNCTION    revoke_token(raw_token)
    """

    def test_revokes_given_token(self, db, token):
        """
        GIVEN   there exists a token in the database
        WHEN    revoke token is called just with the token
        THEN    the revoked flag is set for the token
        """
        raw = decode_token(token)
        revoke_token(raw)
        updated_token = db.session.query(JWTToken).filter_by(jti=raw["jti"]).first()
        assert updated_token.revoked

    def test_revokes_and_removes_token(self, db, token):
        """
        GIVEN   there exists a token in the database
        WHEN    revoke token is called with the token and remove flag
        THEN    the revoked flag is removed from the DB
        """
        raw = decode_token(token)
        revoke_token(raw, True)
        assert 0 == db.session.query(JWTToken).count()

    def test_raises_error_if_token_not_found(self, db):
        """
        GIVEN   there exists no token with a jti
        WHEN    revoke token is called
        THEN    a TokenNotFound is exception is raised
        """
        dummy = {"jti": "dummy_token", "identity": {}}
        with pytest.raises(TokenNotFound):
            revoke_token(dummy)


@pytest.mark.usefixtures("db")
class TestIsTokenRevoked(object):
    """
    FUNCTION    is_token_revoked(decoded_token)
    """

    def test_returns_true_for_revoked(self, token):
        """
        GIVEN   there is a revoked token in the DB
        WHEN    the function is called
        THEN    it returns true
        """
        raw = decode_token(token)
        revoke_token(raw)
        assert is_token_revoked(raw)

    def test_returns_true_for_token_not_found_in_db(self):
        """
        GIVEN   a token is not present in the DB
        WHEN    the function is called
        THEN    it returns true
        """
        dummy = {"jti": "dummy_token"}
        assert is_token_revoked(dummy)

    def test_returns_false_for_active_token(self, token):
        """
        GIVEN   an active token is present in the DB
        WHEN    the function is called
        THEN    it returns false
        """
        raw = decode_token(token)
        assert False == is_token_revoked(raw)
