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
    # Build the callback URL with the exact domain
    callback_url = f"https://{domain}/google_login/callback"

    print("\n" + "="*80)
    print("IMPORTANT: Configure this EXACT URL in Google Cloud Console")
    print("="*80)
    print(f"\nCallback URL: {callback_url}")
    print("\nSteps to configure:")
    print("1. Go to https://console.cloud.google.com/apis/credentials")
    print("2. Click on your OAuth 2.0 Client ID")
    print("3. Add the above URL to 'Authorized redirect URIs'")
    print("4. Click Save and wait 5-10 minutes for changes to take effect")
    print("\nNOTE: The callback URL must match EXACTLY, including:")
    print("- No trailing slash")
    print("- Correct protocol (https://)")
    print("- Exact domain name")
    print("="*80)
    return callback_url.rstrip('/')  # Ensure no trailing slash

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
        # Verify credentials
        client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
        client_secret = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
        if not client_id or not client_secret:
            print("OAuth Error: Missing OAuth credentials")
            return """
                Google OAuth credentials are not configured. Please:
                1. Create OAuth 2.0 credentials in Google Cloud Console
                2. Add GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET to your Repl's Secrets
                3. Try logging in again
            """, 500

        # Get Google provider configuration
        google_provider_cfg = get_google_provider_cfg()
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]

        # Get the callback URL and print setup instructions
        callback_url = get_callback_url()

        # Create OAuth 2 client
        client = get_google_client()

        print(f"Initiating Google OAuth flow with callback URL: {callback_url}")
        
        # Prepare the request URI with explicit parameters
        request_uri = client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=callback_url,
            scope=["openid", "email", "profile"],
            access_type="offline",
            prompt="consent"
        )

        # Log the authorization URL for debugging
        print(f"Authorization URL: {request_uri}")
        
        return redirect(request_uri)
    except requests.exceptions.RequestException as e:
        print(f"OAuth Error - Network error: {str(e)}")
        return "Failed to connect to Google authentication service. Please try again.", 500
    except Exception as e:
        error_msg = str(e)
        print(f"OAuth Error - Login failed: {error_msg}")
        if "redirect_uri_mismatch" in error_msg.lower():
                callback_url = get_callback_url()  # Get the exact callback URL
                return f"""
                    <html>
                    <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px;">
                        <h2 style="color: #d32f2f;">Error: Callback URL Mismatch</h2>
                        <p>The callback URL is not properly configured in Google Cloud Console.</p>
                        <div style="background: #f5f5f5; padding: 20px; border-radius: 4px; margin: 20px 0;">
                            <strong>Required Callback URL:</strong><br>
                            <code style="background: #fff; padding: 10px; display: block; margin: 10px 0;">{callback_url}</code>
                        </div>
                        <h3>Steps to fix:</h3>
                        <ol>
                            <li>Go to <a href="https://console.cloud.google.com/apis/credentials" target="_blank">Google Cloud Console</a></li>
                            <li>Find and edit your OAuth 2.0 Client ID</li>
                            <li>In 'Authorized redirect URIs', add the exact URL shown above</li>
                            <li>Click 'SAVE' at the bottom</li>
                            <li>Wait 5-10 minutes for Google's settings to update</li>
                            <li><a href="/google_login">Try logging in again</a></li>
                        </ol>
                    </body>
                    </html>
                """, 500
        return "An error occurred during login. Please check the application logs.", 500

@google_auth.route("/google_login/callback")
def callback():
    """Handle the Google OAuth callback"""
    try:
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

        # Get callback URL and client
        callback_url = get_callback_url()
        client = get_google_client()

        print(f"Processing OAuth callback with code: {code[:5]}...")
        print(f"Full callback URL: {request.url}")

        # Prepare token request with the correct callback URL
        # Ensure we're using HTTPS for the authorization response URL
        authorization_response = request.url.replace('http://', 'https://')
        token_url, headers, body = client.prepare_token_request(
            token_endpoint,
            authorization_response=authorization_response,
            redirect_url=callback_url,
            code=code
        )

        print(f"Token URL: {token_url}")
        print(f"Callback URL used: {callback_url}")

        # Get access token
        client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
        client_secret = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")

        if not client_id or not client_secret:
            print("OAuth Error - Missing client credentials")
            return "Missing OAuth credentials", 500

        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(client_id, client_secret)
        )

        # Check token response
        if not token_response.ok:
            error_msg = token_response.text
            print(f"OAuth Error - Token response failed: {error_msg}")
            return f"Failed to get access token from Google: {error_msg}", 500

        # Parse token response
        client.parse_request_body_response(json.dumps(token_response.json()))

        # Get user info from Google
        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)

        if not userinfo_response.ok:
            error_msg = userinfo_response.text
            print(f"OAuth Error - User info failed: {error_msg}")
            return f"Failed to get user info from Google: {error_msg}", 500

        # Verify user info
        userinfo = userinfo_response.json()
        if not userinfo.get("email_verified"):
            return "User email not verified by Google.", 400

        # Get user details
        users_email = userinfo["email"]
        users_name = userinfo.get("given_name", users_email.split("@")[0])

        print(f"Successfully authenticated user: {users_email}")

        # Create or update user
        user = User.query.filter_by(email=users_email).first()
        if not user:
            user = User(username=users_name, email=users_email)
            db.session.add(user)
            db.session.commit()
            print(f"Created new user: {users_email}")
        else:
            print(f"Found existing user: {users_email}")

        # Log in user
        login_user(user)
        print(f"User logged in successfully: {users_email}")

        # Redirect to home page
        try:
            target_url = url_for('index', _external=True, _scheme='https')
            print(f"Redirecting to: {target_url}")
            return redirect(target_url)
        except Exception as e:
            print(f"Error generating redirect URL: {str(e)}")
            print("Using fallback redirect to root URL")
            return redirect('/')

    except Exception as e:
        print(f"OAuth Error - Callback failed: {str(e)}")
        return f"Failed to process Google login callback: {str(e)}", 500

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