from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from models import db, User
from routes import routes  # Import Blueprint instead of app reference
from superadmin_routes import superadmin_routes
from admin_routes import admin_routes
from driver_routes import driver_routes
from user_routes import user_routes

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://root:@localhost/secure_app"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "super_secret_key"
app.config["GOOGLE_MAPS_API_KEY"] = "AIzaSyB6tSGQTeFbaS0mxyN-v3ePJ0gojitIIOE"

db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Register Blueprint routes
app.register_blueprint(routes)
app.register_blueprint(superadmin_routes)
app.register_blueprint(admin_routes)
app.register_blueprint(driver_routes)
app.register_blueprint(user_routes)

if __name__ == "__main__":
    # app.run(debug=True)
    app.run("0.0.0.0", port=5000)
