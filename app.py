import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase

# Initialize Flask app
app = Flask(__name__)

# Configure app
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or os.urandom(24)

# Get the Replit domain and port
replit_domain = os.environ.get("REPLIT_DEV_DOMAIN")
server_port = os.environ.get("PORT", "3000")

if not replit_domain:
    print("Warning: REPLIT_DEV_DOMAIN not set. Some features may not work correctly.")
else:
    print(f"Configuring application for domain: {replit_domain}")

# Configure SQLAlchemy and session settings
app.config.update(
    SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL"),
    SQLALCHEMY_ENGINE_OPTIONS={
        "pool_recycle": 300,
        "pool_pre_ping": True,
    },
    # Security settings
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    REMEMBER_COOKIE_SECURE=True,
    REMEMBER_COOKIE_HTTPONLY=True,
    # HTTPS and domain configuration
    PREFERRED_URL_SCHEME="https",
)

# Only set SERVER_NAME if we have a domain
if replit_domain:
    app.config['SERVER_NAME'] = replit_domain

print(f"\nConfigured server name: {replit_domain}")
print(f"Make sure this matches your Google OAuth Callback URL domain exactly")

# Ensure the application can handle both HTTP and HTTPS
if not app.debug:
    app.config['SESSION_COOKIE_SECURE'] = True

# Enable request forwarding with proper HTTPS handling
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(
    app.wsgi_app,
    x_proto=1,  # Number of proxy servers setting the X-Forwarded-Proto header
    x_host=1,   # Number of proxy servers setting the X-Forwarded-Host header
    x_port=1,   # Number of proxy servers setting the X-Forwarded-Port header
    x_prefix=1, # Number of proxy servers setting the X-Forwarded-Prefix header
    x_for=1     # Number of proxy servers setting the X-Forwarded-For header
)

# Ensure all redirects use HTTPS
app.config['PREFERRED_URL_SCHEME'] = 'https'

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