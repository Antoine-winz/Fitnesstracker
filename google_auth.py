import json
import os
import requests
from flask import Blueprint, redirect, request, url_for
from flask_login import login_required, login_user, logout_user, current_user
from oauthlib.oauth2 import WebApplicationClient

# Import models and db after blueprint creation to avoid circular imports
google_auth = Blueprint("google_auth", __name__)

# Initialize OAuth 2 client
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

def get_google_client():
    client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
    if not client_id:
        raise RuntimeError(
            "Google OAuth credentials not configured. "
            "Please set GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET "
            "in your Repl's Secrets tab."
        )
    return WebApplicationClient(client_id)

def get_callback_url():
    """Get the callback URL for Google OAuth"""
    domain = os.environ.get("REPLIT_DEV_DOMAIN")
    if not domain:
        raise RuntimeError(
            "REPLIT_DEV_DOMAIN environment variable is not set. "
            "Please ensure you are running this on Replit."
        )
    callback_url = f"https://{domain}/google_login/callback"
    print(f"OAuth Debug - Generated callback URL: {callback_url}")
    return callback_url

# Print setup instructions
print("""To make Google authentication work:
1. Go to https://console.cloud.google.com/apis/credentials
2. Create a new OAuth 2.0 Client ID
3. Add your callback URL (<your-repl-domain>/google_login/callback) to Authorized redirect URIs
4. Set GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET in your Repl's Secrets tab""")

@google_auth.route("/google_login")
def login():
    """Initiate Google OAuth login flow"""
    if not os.environ.get("GOOGLE_OAUTH_CLIENT_ID"):
        return "Google OAuth client ID not configured. Please check your Repl's Secrets tab.", 500

    try:
        # Get Google provider configuration
        google_provider_cfg = get_google_provider_cfg()
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]
        
        # Get the callback URL
        callback_url = get_callback_url()
        
        # Create OAuth 2 client
        client = get_google_client()
        
        # Prepare the request URI
        request_uri = client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=callback_url,
            scope=["openid", "email", "profile"],
        )
        
        return redirect(request_uri)
    except Exception as e:
        print(f"OAuth Error - Login failed: {str(e)}")
        return "Failed to initialize Google login. Please check the application logs.", 500

@google_auth.route("/google_login/callback")
def callback():
    """Handle the Google OAuth callback"""
    try:
        from app import db
        from models import User

        # Get authorization code from Google
        code = request.args.get("code")
        if not code:
            return "Authorization code not received from Google", 400

        # Get Google provider configuration
        google_provider_cfg = get_google_provider_cfg()
        token_endpoint = google_provider_cfg["token_endpoint"]
        
        # Get callback URL and client
        callback_url = get_callback_url()
        client = get_google_client()
        
        # Prepare token request
        token_url, headers, body = client.prepare_token_request(
            token_endpoint,
            authorization_response=request.url.replace('http://', 'https://'),
            redirect_url=callback_url,
            code=code
        )

        # Get access token
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(os.environ.get("GOOGLE_OAUTH_CLIENT_ID"),
                  os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET"))
        )

        # Check token response
        if not token_response.ok:
            return "Failed to get access token from Google", 500

        # Parse token response
        client.parse_request_body_response(json.dumps(token_response.json()))

        # Get user info from Google
        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)

        if not userinfo_response.ok:
            return "Failed to get user info from Google", 500

        # Verify user info
        userinfo = userinfo_response.json()
        if not userinfo.get("email_verified"):
            return "User email not verified by Google.", 400

        # Get user details
        users_email = userinfo["email"]
        users_name = userinfo.get("given_name", users_email.split("@")[0])

        # Create or update user
        user = User.query.filter_by(email=users_email).first()
        if not user:
            user = User(username=users_name, email=users_email)
            db.session.add(user)
            db.session.commit()

        # Log in user
        login_user(user)
        
        # Redirect to index page
        return redirect(url_for('index', _external=True, _scheme='https'))

    except Exception as e:
        print(f"OAuth Error - Callback failed: {str(e)}")
        return "Failed to process Google login callback", 500

@google_auth.route("/logout")
@login_required
def logout():
    try:
        print(f"Logout - Processing logout for user: {current_user.email if current_user else 'Unknown'}")
        logout_user()
        print("Logout - User session terminated successfully")
        return redirect(url_for("index"))
    except Exception as e:
        print(f"Logout Error: {str(e)}")
        return redirect(url_for("index"))
