# -*- coding: utf-8 -*-
"""The app module, containing the app factory function."""
import sentry_sdk
from flask import Flask, render_template
from flask_admin import Admin
from sentry_sdk import last_event_id
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.rq import RqIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

import peerfeedback.models
from peerfeedback import admin, api, commands, models, public, user
from peerfeedback.api.views import api_blueprint
from peerfeedback.crons import (
    award_ml_grade,
    clear_expired_tokens,
    update_pairing_schedules,
    update_user_reputation,
)
from peerfeedback.extensions import (
    cache,
    cas,
    db,
    debug_toolbar,
    jwt,
    login_manager,
    marsh,
    migrate,
    oauth,
    rq,
    sslify,
)
from peerfeedback.models import User
from peerfeedback.settings import ProdConfig
from peerfeedback.user.jwt_helpers import is_token_revoked


def create_app(config_object=ProdConfig):
    """An application factory, as explained here: http://flask.pocoo.org/docs/patterns/appfactories/.

    :param config_object: The configuration object to use.
    """
    app = Flask(__name__.split(".")[0])
    app.config.from_object(config_object)
    register_extensions(app)
    register_admin(app)
    register_blueprints(app)
    register_errorhandlers(app)
    register_shellcontext(app)
    register_commands(app)
    start_cron_jobs(app)

    sentry_sdk.init(
        dsn=app.config.get("SENTRY_DSN"),
        integrations=[
            FlaskIntegration(),
            RqIntegration(),
            SqlalchemyIntegration(),
            RedisIntegration(),
        ],
    )

    return app


def register_extensions(app):
    """Register Flask extensions."""
    cache.init_app(app)
    db.init_app(app)
    marsh.init_app(app)
    debug_toolbar.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    oauth.init_app(app)
    rq.init_app(app)
    cas.init_app(app)
    login_manager.init_app(app)
    sslify(app)
    return None


def register_admin(app):
    admin_ext = Admin(app, name="peerfeedback", template_mode="bootstrap3")
    admin_ext.add_view(
        admin.views.AppModelView(peerfeedback.models.User, db.session, endpoint="users")
    )
    admin_ext.add_view(admin.views.AppModelView(models.Pairing, db.session))
    admin_ext.add_view(admin.views.AppModelView(models.Feedback, db.session))
    admin_ext.add_view(admin.views.AppModelView(models.Task, db.session))
    admin_ext.add_view(admin.views.AppModelView(models.Comment, db.session))
    admin_ext.add_view(admin.views.AppModelView(models.MetaFeedback, db.session))
    admin_ext.add_view(admin.views.AppModelView(models.Study, db.session))
    admin_ext.add_view(admin.views.LoginView(name="Login", endpoint="login"))
    admin_ext.add_view(admin.views.LogoutView(name="Logout", endpoint="logout"))


def register_blueprints(app):
    """Register Flask blueprints."""
    app.register_blueprint(public.views.blueprint)
    app.register_blueprint(user.views.blueprint)
    app.register_blueprint(api_blueprint)
    return None


def register_errorhandlers(app):
    """Register error handlers."""

    def render_error(error):
        """Render error template."""
        # If a HTTPException, pull the `code` attribute; default to 500
        error_code = getattr(error, "code", 500)
        if error_code == 500:
            return render_template("500.html", sentry_event_id=last_event_id()), 500
        return render_template("{0}.html".format(error_code)), error_code

    for errcode in [401, 404, 500]:
        app.errorhandler(errcode)(render_error)
    return None


def register_shellcontext(app):
    """Register shell context objects."""

    def shell_context():
        """Shell context objects."""
        return {"db": db, "User": peerfeedback.models.User}

    app.shell_context_processor(shell_context)


def register_commands(app):
    """Register Click commands."""
    app.cli.add_command(commands.test)
    app.cli.add_command(commands.lint)
    app.cli.add_command(commands.clean)
    app.cli.add_command(commands.urls)
    app.cli.add_command(commands.init_canvas)
    app.cli.add_command(commands.add_admin)
    app.cli.add_command(commands.add_rubric)
    app.cli.add_command(commands.setup_study)
    app.cli.add_command(commands.preview_pairing)


def start_cron_jobs(app):
    """Starts the application cron jobs"""
    clear_expired_tokens.cron(app.config["CRON_PATTERN"], "clear-expired-jwt")
    award_ml_grade.cron(app.config["CRON_PATTERN"], "award-ml-grade")
    update_pairing_schedules.cron(
        app.config["CRON_PATTERN"], "update-pairing-schedules"
    )
    update_user_reputation.cron(
        app.config["CRON_PATTERN"],
        "update-user-reputation",
    )


# --------------------------------------------------------------------------- #
# Callback declarations for the extensions
# --------------------------------------------------------------------------- #
@jwt.token_in_blacklist_loader
def check_if_token_revoked(decoded_token):
    return is_token_revoked(decoded_token)


@jwt.user_loader_callback_loader
def get_jwt_user(identity):
    return User.query.get(identity["id"])


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)
