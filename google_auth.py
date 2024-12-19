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
    try:
        # Check for required environment variables
        client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
        client_secret = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
        
        if not client_id or not client_secret:
            error_msg = "Google OAuth credentials not configured. Please set GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET in your Repl's Secrets tab."
            print(f"OAuth Error - {error_msg}")
            return error_msg, 500
            
        # Get Google provider configuration
        try:
            google_provider_cfg = get_google_provider_cfg()
            authorization_endpoint = google_provider_cfg["authorization_endpoint"]
        except Exception as e:
            error_msg = "Failed to fetch Google OAuth configuration"
            print(f"OAuth Error - {error_msg}: {str(e)}")
            return error_msg, 500
        
        # Create OAuth 2 client and get callback URL
        client = WebApplicationClient(client_id)
        callback_url = get_callback_url()
        
        print(f"OAuth Debug - Starting login process")
        print(f"OAuth Debug - Client ID: {client_id[:8]}...")
        print(f"OAuth Debug - Callback URL: {callback_url}")
        
        # Prepare the request URI
        request_uri = client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=callback_url,
            scope=["openid", "email", "profile"],
            extras_params={"access_type": "offline"}
        )
        
        print(f"OAuth Debug - Authorization URL generated successfully")
        return redirect(request_uri)
        
    except Exception as e:
        error_msg = f"OAuth Error - Login failed: {str(e)}"
        print(error_msg)
        return """
            Failed to initialize Google login. Please ensure:
            1. You've configured the OAuth credentials in Google Cloud Console
            2. Added the correct callback URL to authorized redirect URIs
            3. Set GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET in your Repl's Secrets tab
        """, 500

@google_auth.route("/google_login/callback")
def callback():
    try:
        # Import here to avoid circular imports
        from app import db
        from models import User

        # Get authorization code from Google
        code = request.args.get("code")
        if not code:
            print("OAuth Error - No authorization code received")
            return "Authorization code not received from Google", 400

        # Get Google provider configuration
        google_provider_cfg = get_google_provider_cfg()
        token_endpoint = google_provider_cfg["token_endpoint"]
        
        # Create OAuth 2 client and get callback URL
        client = get_google_client()
        callback_url = get_callback_url()
        
        print(f"OAuth Debug - Processing callback with code: {code[:10]}...")
        
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

        if not token_response.ok:
            print(f"OAuth Error - Token request failed: {token_response.text}")
            return "Failed to get access token from Google", 500

        # Parse token response
        client.parse_request_body_response(json.dumps(token_response.json()))

        # Get user info
        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)

        if not userinfo_response.ok:
            print(f"OAuth Error - User info request failed: {userinfo_response.text}")
            return "Failed to get user info from Google", 500

        userinfo = userinfo_response.json()
        if not userinfo.get("email_verified"):
            print("OAuth Error - Email not verified")
            return "User email not verified by Google.", 400

        users_email = userinfo["email"]
        users_name = userinfo.get("given_name", users_email.split("@")[0])
        print(f"OAuth Debug - Retrieved user info for: {users_email}")

        # Create or get user
        try:
            user = User.query.filter_by(email=users_email).first()
            if not user:
                user = User(username=users_name, email=users_email)
                db.session.add(user)
                db.session.commit()
                print(f"OAuth Debug - Created new user: {users_email}")
            
            # Log in user and redirect
            login_user(user)
            print(f"OAuth Debug - Successfully logged in user: {users_email}")
            return redirect(url_for('index', _external=True, _scheme='https'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Database Error - Failed to handle user: {str(e)}")
            return "Failed to create or update user profile", 500

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
