from functools import wraps
from flask import redirect, url_for
from flask_login import current_user, login_required

def role_required(role_name):
    def decorator(view_function):
        @wraps(view_function)
        @login_required
        def wrapper(*args, **kwargs):
            if current_user.role != role_name:
                return redirect(url_for("routes.index"))
            return view_function(*args, **kwargs)
        return wrapper
    return decorator
