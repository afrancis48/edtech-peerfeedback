# -*- coding: utf-8 -*-
"""Public section, including homepage and signup."""
import re

from flask import Blueprint

blueprint = Blueprint("public", __name__, static_folder="../static")


@blueprint.route("/")
def home():
    return blueprint.send_static_file("index.html")


@blueprint.route("/app/<path:path>")
def frontend(path):
    filetypes = re.compile(r".*\.(?:css|ico|svg|png|js|map|json)$", re.IGNORECASE)
    if re.match(filetypes, path):
        return blueprint.send_static_file(path)
    return blueprint.send_static_file("index.html")
