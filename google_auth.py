import json
import os
import requests
from flask import Blueprint, redirect, request, url_for
from flask_login import login_required, login_user, logout_user
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
    if not os.environ.get("REPLIT_DEV_DOMAIN"):
        raise RuntimeError(
            "REPLIT_DEV_DOMAIN environment variable is not set. "
            "Please ensure you are running this on Replit."
        )
    return url_for("google_auth.callback", _external=True, _scheme="https")

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
        from app import db  # Import here to avoid circular imports
        
        if not os.environ.get("GOOGLE_OAUTH_CLIENT_ID") or not os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET"):
            raise RuntimeError("Google OAuth credentials not configured")
            
        # Get Google provider configuration
        google_provider_cfg = get_google_provider_cfg()
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]
        
        # Create OAuth 2 client and get callback URL
        client = get_google_client()
        callback_url = get_callback_url()
        
        print(f"OAuth Debug - Starting login for callback URL: {callback_url}")
        
        # Prepare the request URI
        request_uri = client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=callback_url,
            scope=["openid", "email", "profile"],
        )
        
        print(f"OAuth Debug - Authorization URL generated successfully")
        return redirect(request_uri)
        
    except Exception as e:
        print(f"OAuth Error - Login failed: {str(e)}")
        return "Failed to initialize Google login. Please check the application logs and ensure OAuth credentials are properly configured.", 500

@google_auth.route("/google_login/callback")
def callback():
    try:
        # Import here to avoid circular imports
        from app import db
        from models import User

        # Get authorization code from Google
        code = request.args.get("code")
        if not code:
            return "Authorization code not received from Google", 400

        # Get Google provider configuration
        google_provider_cfg = get_google_provider_cfg()
        token_endpoint = google_provider_cfg["token_endpoint"]
        
        # Get the callback URL
        callback_url = get_callback_url()
        
        # Create OAuth 2 client
        client = get_google_client()
        
        # Prepare and send token request
        token_url, headers, body = client.prepare_token_request(
            token_endpoint,
            authorization_response=request.url.replace('http://', 'https://'),
            redirect_url=callback_url,
            code=code,
        )
        
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(os.environ.get("GOOGLE_OAUTH_CLIENT_ID"), 
                  os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")),
        )

        # Parse the token response
        client.parse_request_body_response(json.dumps(token_response.json()))

        # Get user info from Google
        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)

        # Verify the user info
        userinfo = userinfo_response.json()
        if userinfo.get("email_verified"):
            users_email = userinfo["email"]
            users_name = userinfo.get("given_name", users_email.split("@")[0])
        else:
            return "User email not available or not verified by Google.", 400

        # Create or get user with proper error handling
        try:
            user = User.query.filter_by(email=users_email).first()
            if not user:
                # Create new user profile
                user = User(
                    username=users_name,
                    email=users_email
                )
                db.session.add(user)
                try:
                    db.session.commit()
                    print(f"Created new user: {users_email}")
                except Exception as e:
                    print(f"Error creating user: {str(e)}")
                    db.session.rollback()
                    return "Failed to create user profile", 500
            
            # Log in the user
            login_user(user)
            print(f"Successfully logged in user: {users_email}")
            
            # Explicitly return to the index route
            return redirect(url_for('index', _external=True))
            
        except Exception as e:
            print(f"Error in user creation/login: {str(e)}")
            return "Authentication failed. Please try again.", 500
    except Exception as e:
        print(f"Error in callback route: {str(e)}")
        return "Failed to process Google login callback. Please try again.", 500

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
