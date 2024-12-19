import os
from flask import Flask, redirect, url_for, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)

# Configure Flask app
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "a secret key"
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize extensions
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Register Google OAuth blueprint
from google_auth import google_auth
app.register_blueprint(google_auth)

@app.route('/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    return render_template('login.html')

# Protect all routes except login
@app.before_request
def check_user_auth():
    if not current_user.is_authenticated and request.endpoint and request.endpoint != 'login' and \
       not request.endpoint.startswith('google_auth.') and \
       request.endpoint not in ['static']:
        return redirect(url_for('login'))

# Initialize database and routes
with app.app_context():
    import models
    import routes
    db.create_all()