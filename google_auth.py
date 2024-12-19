import json
import os
import requests
from flask import Blueprint, redirect, request, url_for
from flask_login import login_required, login_user, logout_user
from oauthlib.oauth2 import WebApplicationClient

# Import models and db after blueprint creation to avoid circular imports
google_auth = Blueprint("google_auth", __name__)

try:
    GOOGLE_CLIENT_ID = os.environ["GOOGLE_OAUTH_CLIENT_ID"]
    GOOGLE_CLIENT_SECRET = os.environ["GOOGLE_OAUTH_CLIENT_SECRET"]
except KeyError as e:
    print(f"Missing required environment variable: {e}")
    print("Please set up Google OAuth credentials in your Repl's Secrets tab")
    GOOGLE_CLIENT_ID = None
    GOOGLE_CLIENT_SECRET = None

GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

def get_google_client():
    if not GOOGLE_CLIENT_ID:
        raise RuntimeError(
            "Google OAuth credentials not configured. "
            "Please set GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET "
            "in your Repl's Secrets tab."
        )
    return WebApplicationClient(GOOGLE_CLIENT_ID)

client = None
if GOOGLE_CLIENT_ID:
    client = get_google_client()

# Get the appropriate callback URL based on environment
def get_callback_url():
    if os.environ.get('REPLIT_DEV_DOMAIN'):
        domain = os.environ.get('REPLIT_DEV_DOMAIN')
    else:
        # Fallback to request.host_url for deployment
        domain = request.host.replace('http://', '').replace('https://', '')
    return f"https://{domain}/google_login/callback"

# Print setup instructions
print(f"""To make Google authentication work:
1. Go to https://console.cloud.google.com/apis/credentials
2. Create a new OAuth 2.0 Client ID
3. Add {get_callback_url()} to Authorized redirect URIs
4. Set GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET in your Repl's Secrets tab""")

@google_auth.route("/google_login")
def login():
    try:
        if not client:
            client = get_google_client()
        
        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]
        
        callback_url = get_callback_url()
        print(f"OAuth Debug - Callback URL: {callback_url}")
        
        request_uri = client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=callback_url,
            scope=["openid", "email", "profile"],
        )
        return redirect(request_uri)
    except Exception as e:
        print(f"Error in login route: {str(e)}")
        return "Failed to initialize Google login. Please ensure OAuth credentials are properly configured.", 500

@google_auth.route("/google_login/callback")
def callback():
    try:
        # Import here to avoid circular imports
        from app import db
        from models import User

        if not client:
            client = get_google_client()

        code = request.args.get("code")
        if not code:
            return "Authorization code not received from Google", 400

        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        token_endpoint = google_provider_cfg["token_endpoint"]
        
        callback_url = get_callback_url()
        
        # Ensure the authorization response URL uses HTTPS
        full_callback_url = request.url
        if full_callback_url.startswith('http://'):
            full_callback_url = full_callback_url.replace('http://', 'https://', 1)
        
        print(f"OAuth Debug - Processing callback with URL: {full_callback_url}")
        
        token_url, headers, body = client.prepare_token_request(
            token_endpoint,
            authorization_response=full_callback_url,
            redirect_url=callback_url,
            code=code,
        )
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
        )

        client.parse_request_body_response(json.dumps(token_response.json()))

        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)

        userinfo = userinfo_response.json()
        if userinfo.get("email_verified"):
            users_email = userinfo["email"]
            users_name = userinfo["given_name"]
        else:
            return "User email not available or not verified by Google.", 400

        user = User.query.filter_by(email=users_email).first()
        if not user:
            user = User(username=users_name, email=users_email)
            db.session.add(user)
            db.session.commit()

        login_user(user)
        return redirect(url_for("index"))
    except Exception as e:
        print(f"Error in callback route: {str(e)}")
        return "Failed to process Google login callback. Please try again.", 500

@google_auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))
