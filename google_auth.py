import json
import os
import requests
from flask import Blueprint, redirect, request, url_for, current_app
from flask_login import login_required, login_user, logout_user
from oauthlib.oauth2 import WebApplicationClient

GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
google_auth = Blueprint("google_auth", __name__)

def get_google_provider_cfg():
    try:
        response = requests.get(GOOGLE_DISCOVERY_URL)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        current_app.logger.error(f"Error fetching Google provider config: {str(e)}")
        raise

def get_callback_url():
    domain = os.environ.get("REPLIT_DEV_DOMAIN")
    if not domain:
        current_app.logger.error("REPLIT_DEV_DOMAIN not configured")
        return None
    return f"https://{domain}/google_login/callback"

@google_auth.route("/google_login")
def login():
    try:
        # Get Google provider configuration
        google_provider_cfg = get_google_provider_cfg()
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]

        # Initialize client with credentials
        client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
        if not client_id:
            current_app.logger.error("Google OAuth client ID not configured")
            return "Google OAuth client ID not configured", 500

        client = WebApplicationClient(client_id)

        # Get callback URL
        callback_url = get_callback_url()
        if not callback_url:
            return "Callback URL configuration error", 500

        current_app.logger.info(f"Login callback URL: {callback_url}")

        # Create authorization request URL
        request_uri = client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=callback_url,
            scope=["openid", "email", "profile"]
        )

        return redirect(request_uri)
    except Exception as e:
        current_app.logger.error(f"Login error: {str(e)}")
        return f"An error occurred during login setup: {str(e)}", 500

@google_auth.route("/google_login/callback")
def callback():
    try:
        # Get authorization code
        code = request.args.get("code")
        if not code:
            current_app.logger.error("Authorization code not received")
            return "Authorization code not received", 400

        # Initialize client
        client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
        client_secret = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
        if not client_id or not client_secret:
            current_app.logger.error("OAuth credentials not configured")
            return "OAuth credentials not configured", 500

        # Get callback URL
        callback_url = get_callback_url()
        if not callback_url:
            return "Callback URL configuration error", 500

        current_app.logger.info(f"Callback URL: {callback_url}")

        client = WebApplicationClient(client_id)

        # Get token endpoint
        google_provider_cfg = get_google_provider_cfg()
        token_endpoint = google_provider_cfg["token_endpoint"]

        # Prepare token request with exact URL matching
        token_url, headers, body = client.prepare_token_request(
            token_endpoint,
            authorization_response=callback_url + "?" + request.query_string.decode(),
            redirect_url=callback_url,
            code=code
        )

        # Exchange code for tokens
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(client_id, client_secret),
        )

        # Parse token response
        client.parse_request_body_response(json.dumps(token_response.json()))

        # Get user info
        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)

        if not userinfo_response.ok:
            current_app.logger.error("Failed to get user info")
            return "Failed to get user info", 500

        userinfo = userinfo_response.json()
        if not userinfo.get("email_verified"):
            return "User email not verified by Google.", 400

        # Get user info
        users_email = userinfo["email"]
        users_name = userinfo.get("given_name", users_email.split("@")[0])

        # Create or get user
        from app import db
        from models import User

        user = User.query.filter_by(email=users_email).first()
        if not user:
            user = User(username=users_name, email=users_email)
            db.session.add(user)
            db.session.commit()

        # Login user
        login_user(user)
        return redirect(url_for('index'))

    except Exception as e:
        current_app.logger.error(f"Callback error: {str(e)}")
        return f"An error occurred during login: {str(e)}", 500

@google_auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))