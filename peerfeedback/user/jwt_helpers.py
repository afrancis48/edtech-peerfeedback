from datetime import datetime

from sqlalchemy.orm.exc import NoResultFound
from flask_jwt_extended import decode_token

from peerfeedback.extensions import db
from peerfeedback.exceptions import TokenNotFound
from peerfeedback.models import JWTToken


def _epoch_utc_to_datetime(epoch_utc):
    """
    Helper function for converting epoch timestamps (as stored in JWTs) into
    python datetime objects (which are easier to use with sqlalchemy).
    """
    return datetime.fromtimestamp(epoch_utc)


def add_token_to_database(encoded_token, identity_claim):
    """
    Adds a new token to the database. It is not revoked when it is added.
    :param identity_claim:
    """
    decoded_token = decode_token(encoded_token)
    jti = decoded_token["jti"]
    token_type = decoded_token["type"]
    user_identity = decoded_token[identity_claim]
    expires = _epoch_utc_to_datetime(decoded_token["exp"])
    revoked = False

    db_token = JWTToken.create(
        jti=jti,
        token_type=token_type,
        user_identity=user_identity["username"],
        expires=expires,
        revoked=revoked,
    )
    db.session.add(db_token)
    db.session.commit()


def is_token_revoked(decoded_token):
    """
    Checks if the given token is revoked or not. Because we are adding all the
    tokens that we create into this database, if the token is not present
    in the database we are going to consider it revoked, as we don't know where
    it was created.
    """
    jti = decoded_token["jti"]
    try:
        token = JWTToken.query.filter_by(jti=jti).one()
        return token.revoked
    except NoResultFound:
        return True


def get_user_tokens(user_identity):
    """
    Returns all of the tokens, revoked and unrevoked, that are stored for the
    given user
    """
    return JWTToken.query.filter_by(user_identity=user_identity).all()


def clear_token(jti, delete=False):
    try:
        token = JWTToken.query.filter_by(jti=jti).one()
        token.revoked = True
        if delete:
            db.session.delete(token)
        db.session.commit()
    except NoResultFound:
        raise TokenNotFound("Could not find token {}".format(jti))


def revoke_token(raw_token, remove=False):
    """
    Revokes the given token. Raises a TokenNotFound error if the token does
    not exist in the database
    """
    jti = raw_token["jti"]
    refresh_jti = raw_token["identity"].get("refresh_jti", None)
    clear_token(jti, remove)
    if refresh_jti:
        clear_token(refresh_jti, remove)


def prune_database():
    """
    Delete tokens that have expired from the database.
    TODO Setup a automated way to run this
    """
    now = datetime.now()
    expired = JWTToken.query.filter(JWTToken.expires < now).all()
    for token in expired:
        db.session.delete(token)
    db.session.commit()
