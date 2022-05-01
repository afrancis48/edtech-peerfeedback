import os

from flask import redirect, url_for, abort

from flask_admin import BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user, login_user, logout_user

from peerfeedback.models import User

from .forms import LoginForm


class AppModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for("admin.login"))


class LoginView(BaseView):
    def is_accessible(self):
        return not current_user.is_authenticated

    @expose("/", methods=["GET", "POST"])
    def index(self):
        form = LoginForm()
        if form.validate_on_submit():
            if form.username.data == "admin" and form.password.data == os.environ.get(
                "ADMIN_PASSWORD"
            ):
                user = User.query.filter(User.username == "admin").first()
                if not user:
                    return "Admin User not present"
                login_user(user)
            else:
                return abort(401)

            return redirect(url_for("admin.index"))
        return self.render("admin/login.html", form=form)


class LogoutView(BaseView):
    def is_accessible(self):
        return current_user.is_authenticated

    @expose("/")
    def index(self):
        logout_user()
        return redirect(url_for("admin.index"))
