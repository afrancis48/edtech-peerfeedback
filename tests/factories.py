# -*- coding: utf-8 -*-
"""Factories to help in tests."""
from factory import Sequence
from factory.alchemy import SQLAlchemyModelFactory

from peerfeedback.database import db
from peerfeedback.models import User
from peerfeedback.user.views import create_access_token


class BaseFactory(SQLAlchemyModelFactory):
    """Base factory."""

    class Meta:
        """Factory configuration."""

        abstract = True
        sqlalchemy_session = db.session


class UserFactory(BaseFactory):
    """User factory."""

    canvas_id = Sequence(lambda n: n)
    username = Sequence(lambda n: "user{0}".format(n))
    email = Sequence(lambda n: "user{0}@example.com".format(n))
    active = True

    class Meta:
        """Factory configuration."""

        model = User


def token(user):
    user_obj = User.query.get(user) if isinstance(user, int) else user
    return dict(Authorization="Bearer " + create_access_token(user_obj.as_dict()))
