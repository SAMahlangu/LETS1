from flask import Blueprint, render_template
from decorators import role_required

user_routes = Blueprint("user_routes", __name__, url_prefix="/user")

@user_routes.route("/dashboard")
@role_required("user")
def user_dashboard():
    return render_template("user/dashboard.html")
