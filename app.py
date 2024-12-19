import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase

# Initialize Flask app
app = Flask(__name__)

# Configure app
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or os.urandom(24)
app.config.update(
    SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL"),
    SQLALCHEMY_ENGINE_OPTIONS={
        "pool_recycle": 300,
        "pool_pre_ping": True,
    },
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    REMEMBER_COOKIE_SECURE=True,
    REMEMBER_COOKIE_HTTPONLY=True,
    PREFERRED_URL_SCHEME="https"  # Force HTTPS for URL generation
)

# Ensure HTTPS for all redirects
if os.environ.get("REPLIT_DEV_DOMAIN"):
    app.config["SERVER_NAME"] = os.environ.get("REPLIT_DEV_DOMAIN")

# Initialize SQLAlchemy with custom base
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "google_auth.login"
login_manager.login_message = "Please log in to access this page."

@login_manager.user_loader
def load_user(user_id):
    from models import User
    try:
        return User.query.get(int(user_id))
    except:
        return None

# Register blueprints and create tables
with app.app_context():
    import models
    import routes
    from google_auth import google_auth
    app.register_blueprint(google_auth)
    db.create_all()
