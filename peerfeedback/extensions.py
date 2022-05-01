# -*- coding: utf-8 -*-
"""Extensions module. Each extension is initialized in the app factory located in app.py."""
from flask_caching import Cache
from flask_debugtoolbar import DebugToolbarExtension
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_sslify import SSLify
from flask_rq2 import RQ
from cas_client import CASClient
from flask_login import LoginManager
from flask_marshmallow import Marshmallow
from authlib.flask.client import OAuth
from peerfeedback.settings import Config


# --------------------------------------------------------------------------- #
# CAS class is the flask plugin version of the CASClient for cas auth.
# --------------------------------------------------------------------------- #
class CAS(object):
    def __init__(self, app=None):
        self.client = None
        if app:
            self.init_app(app)

    def init_app(self, app):
        self.client = CASClient(app.config.get("CAS_SERVER"))


db = SQLAlchemy()
migrate = Migrate()
cache = Cache()
debug_toolbar = DebugToolbarExtension()
jwt = JWTManager()
oauth = OAuth()
canvas_oauth = oauth.register("Canvas", **Config.CANVAS)
rq = RQ(default_timeout=240)
sslify = SSLify
login_manager = LoginManager()
cas = CAS()
marsh = Marshmallow()
