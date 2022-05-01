# -*- coding: utf-8 -*-
"""User views."""
import urllib.parse
from datetime import datetime, timedelta, timezone

import requests
from canvasapi import Canvas
from flask import Blueprint, abort
from flask import current_app as app
from flask import (jsonify, make_response, redirect, render_template, request,
                   url_for)
from flask_jwt_extended import (create_access_token, create_refresh_token,
                                decode_token, get_jwt_identity, get_raw_jwt,
                                jwt_refresh_token_required, jwt_required)
from flask_restful import Api, marshal
from peerfeedback.api.utils import get_canvas_client
from peerfeedback.exceptions import TokenNotFound
from peerfeedback.extensions import canvas_oauth, cas
from peerfeedback.models import User, UserSettings
from peerfeedback.user.jwt_helpers import (add_token_to_database,
                                           is_token_revoked, revoke_token)
from peerfeedback.user.resource import (UserResource, UserSettingsResource,
                                        user_fields)
from peerfeedback.utils import update_canvas_token

blueprint = Blueprint("user", __name__, url_prefix="/users", static_folder="../static")
user_api = Api(blueprint)
user_api.add_resource(UserSettingsResource, "/settings/")
user_api.add_resource(UserResource, "/profile/")


@blueprint.route("/oauth-authorized/")
def oauth_authorized():
    try:
        resp = canvas_oauth.authorize_access_token()
    except Exception as e:
        heading = "Login failed !!!"
        error = "Message from Canvas: {0}".format(str(e))
        return render_template("message.html", heading=heading, error=error)

    if not resp or request.args.get("error") == "access_denied":
        heading = "Login failed !!!"
        error = "You did not authorize the app to connect to your Canvas "
        error += "account. Kindly click Login and allow access to use the app."
        return render_template("message.html", heading=heading, error=error)

    user = User.query.filter_by(canvas_id=resp["user"]["id"]).one_or_none()
    if not user:
        canvas_api = Canvas(app.config.get("CANVAS_API_URL"), resp["access_token"])
        canvas_user = canvas_api.get_user(resp["user"]["id"])
        profile = canvas_user.get_profile()

        user = User.create(
            avatar_url=profile.get("avatar_url", None),
            bio=profile.get("bio", None),
            canvas_id=profile["id"],
            email=profile["primary_email"],
            name=profile["name"],
            username=profile["login_id"],
            real_name=profile["name"],
        )
        UserSettings.create(user_id=user.id)

    # NOTE: IMPORTANT - In a ideal use case, we would remove the old oauth token
    # only when the user deletes their account or revokes it from Canvas.
    # Despite Canvas being not an identity provider, this app relies on Canvas
    # for user authentication. So the way to do it is by doing a OAuth
    # verification. So old tokens are deleted and new ones added to the DB
    if user.canvas_access_token:
        # If the user already has a access token, logout the previous session
        # Send a delete request to the oauth endpoint to ask canvas to logout
        url = app.config.get("CANVAS")["access_token_url"]
        token = "Bearer " + user.canvas_access_token
        requests.delete(url, headers={"Authorization": token})

    user.canvas_access_token = resp["access_token"]
    user.canvas_refresh_token = resp["refresh_token"]
    user.canvas_expiration_time = datetime.now(tz=timezone.utc) + timedelta(minutes=59)
    user.save()
    return redirect_to_dashboard_with_tokens(user)


def redirect_to_dashboard_with_tokens(user):
    token_expiry = datetime.now(tz=timezone.utc) + timedelta(minutes=15)
    if token_expiry > user.canvas_expiration_time:
        update_canvas_token(user)
    refresh_token = create_refresh_token(identity=user.as_dict())
    identity = user.as_dict()
    identity["refresh_jti"] = decode_token(refresh_token)["jti"]
    access_token = create_access_token(identity=identity)
    add_token_to_database(access_token, app.config["JWT_IDENTITY_CLAIM"])
    add_token_to_database(refresh_token, app.config["JWT_IDENTITY_CLAIM"])

    response = make_response(redirect(url_for("public.frontend", path="dashboard")))
    expire = datetime.now(tz=timezone.utc)
    expire = expire + timedelta(minutes=5)
    # TODO add secure=True to the following line when upgrading to HTTPS
    response.set_cookie("access_token", access_token, expires=expire)
    response.set_cookie("refresh_token", refresh_token, expires=expire)
    return response


@blueprint.route("/login/refresh/", methods=["POST"])
@jwt_refresh_token_required
def refresh_access_token():
    identity = get_jwt_identity()
    refresh_jwt = get_raw_jwt()
    if is_token_revoked(refresh_jwt):
        return abort(401)
    identity["refresh_jti"] = refresh_jwt["jti"]
    user = User.query.get(identity["id"])
    token_expiry_time = datetime.now(tz=timezone.utc) + timedelta(minutes=15)
    if token_expiry_time > user.canvas_expiration_time:
        update_canvas_token(user)
    token = create_access_token(identity=identity)
    return jsonify({"access_token": token})


@blueprint.route("/logout/", methods=["POST"])
@jwt_required
def logout():
    """Logout."""
    try:
        revoke_token(get_raw_jwt(), True)
    except TokenNotFound:
        # This should be logged somewhere
        return jsonify({"status": "error", "msg": "Invalid Token"})

    response = make_response("OK")
    expire = datetime.now()
    expire = expire - timedelta(minutes=60)
    response.set_cookie("access_token", "", expires=expire)
    response.set_cookie("refresh_token", "", expires=expire)
    return response


@blueprint.route("/<int:user_id>/profile/")
@jwt_required
def user_profile(user_id):
    user = User.query.get(user_id)

    if not user:
        return abort(404)

    token_expiry_time = datetime.now(tz=timezone.utc) + timedelta(minutes=15)
    if token_expiry_time > user.canvas_expiration_time:
        update_canvas_token(user)

    canvas = get_canvas_client(user.canvas_access_token)
    canvas_user = canvas.get_user(user.canvas_id)
    profile = canvas_user.get_profile()

    avatar_url = profile.get("avatar_url", None)
    bio = profile.get("bio", None)

    if user.avatar_url != avatar_url or user.bio != bio:
        user.update(avatar_url=avatar_url, bio=bio)

    return jsonify(marshal(user, user_fields))


@blueprint.route("/login/")
def login():
    ticket = request.args.get("ticket")
    login_type = app.config.get("LOGIN_TYPE")
    if login_type == "canvas_oauth":
        redirect_uri = url_for("user.oauth_authorized", _external=True)
        return canvas_oauth.authorize_redirect(redirect_uri)
    if login_type == "cas" and ticket:
        try:
            cas_response = cas.client.perform_service_validate(
                ticket=ticket,
                service_url=urllib.parse.urljoin(
                    request.host_url, url_for("user.login")
                ),
            )
        except:
            return abort(401)

        if cas_response and cas_response.success:
            user = User.query.filter_by(username=cas_response.user).first()

            if not user or not (
                user.canvas_access_token and user.canvas_expiration_time
            ):
                redirect_uri = url_for("user.oauth_authorized", _external=True)
                return canvas_oauth.authorize_redirect(redirect_uri)

            # TODO: If token is really old, refresh token might fail. This is hackish, should be improved later. 
            if user.canvas_expiration_time < datetime.now(tz=timezone.utc) - timedelta(days=30):
                redirect_uri = url_for("user.oauth_authorized", _external=True)
                return canvas_oauth.authorize_redirect(redirect_uri)

            return redirect_to_dashboard_with_tokens(user)

    elif app.config.get("LOGIN_TYPE") == "cas":
        cas_login_url = cas.client.get_login_url(
            service_url=urllib.parse.urljoin(request.host_url, url_for("user.login"))
        )
        return redirect(cas_login_url)
