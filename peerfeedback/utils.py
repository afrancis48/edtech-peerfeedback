# -*- coding: utf-8 -*-
"""Helper utilities and decorators."""
import re
import os.path
from datetime import datetime, timezone, timedelta

import requests
from flask import current_app as app


def is_valid_email(email):
    if re.match(
        r"^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$", email
    ):
        return True
    return False


def get_pseudo_names():
    """Returns a generator that cycles through the names from naems.txt

    :return: a generator which generates names
    """
    names = []

    dir = os.path.dirname(__file__)
    with open(os.path.join(dir, "resources", "pseudo_names.txt"), "r") as fp:
        for line in fp:
            names.append(line.strip())

    return names


def update_canvas_token(user):
    url = app.config.get("CANVAS")["access_token_url"]
    response = requests.post(
        url,
        data={
            "grant_type": "refresh_token",
            "refresh_token": user.canvas_refresh_token,
            "client_id": app.config.get("CANVAS")["client_id"],
            "client_secret": app.config.get("CANVAS")["client_secret"],
        },
    )
    data = response.json()
    user.canvas_access_token = data["access_token"]
    user.canvas_expiration_time = datetime.now(tz=timezone.utc) + timedelta(minutes=59)
    user.save()
    assert user.canvas_id == data["user"]["id"]
