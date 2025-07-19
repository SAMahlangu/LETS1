from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, Employee, Car, Trailer, JobCard
from werkzeug.security import generate_password_hash, check_password_hash
from superadmin_routes import superadmin_routes

routes = Blueprint("routes", __name__)  # Define a Blueprint for routes

@routes.route("/")
@routes.route("/index")
def index():
    return render_template("login.html")


############### Start Login ################

@routes.route("/login", methods=["POST"])
def login():
    username = request.form["email"]
    password = request.form["password"]
    hash_password  = generate_password_hash(password)

    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password_hash, password):  # Replace with hashed password validation
        login_user(user)

        if user.role == "super_admin":
            return redirect(url_for("superadmin_routes.super_admin_dashboard"))
        elif user.role == "admin":
            return redirect(url_for("routes.admin_dashboard"))
        else:
            return redirect(url_for("driver_routes.driver_portal"))

    return "Invalid Credentials"

@routes.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("routes.index"))


############### End Login ################


############### End SuperAdmin ################

############### Start Admin ################
@routes.route("/admin")
@login_required
def admin_dashboard():
    if not current_user.role == "admin":
        return redirect(url_for("routes.index"))
    return render_template("admin/dashboard.html")

@routes.route("/user")
@login_required
def user_dashboard():
    if not current_user.role == "user":
        return redirect(url_for("routes.index"))
    return render_template("user/dashboard.html")

@routes.route("/settings")
@login_required
def settings():
    return "Welcome to Settings"


############### End Admin ################

############### Start Driver ################
# Driver dashboard is now handled by driver_routes.py

@routes.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]

        # Hash password before saving
        hashed_password = generate_password_hash(password)

        new_user = User(username=username, password_hash=hashed_password, role=role)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("routes.login"))  # ✅ Correct, references Blueprint name


    return render_template("register.html")