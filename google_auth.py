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
    # Don't include port number as Replit handles HTTPS routing
    domain = "5756e563-39aa-4fad-b854-e0d017300d94-00-pwefu4ofvfrn.janeway.replit.dev"
    return f"https://{domain}/oauth2callback"

@google_auth.route("/login")
def login():
    try:
        google_provider_cfg = get_google_provider_cfg()
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]

        client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
        if not client_id:
            current_app.logger.error("Google OAuth client ID not configured")
            return "Google OAuth client ID not configured", 500

        client = WebApplicationClient(client_id)
        callback_url = get_callback_url()

        request_uri = client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=callback_url,
            scope=["openid", "email", "profile"]
        )

        current_app.logger.info(f"Starting OAuth flow with callback URL: {callback_url}")
        return redirect(request_uri)

    except Exception as e:
        current_app.logger.error(f"Login error: {str(e)}")
        return f"An error occurred during login setup: {str(e)}", 500

@google_auth.route("/oauth2callback")
def callback():
    try:
        code = request.args.get("code")
        if not code:
            current_app.logger.error("No authorization code received")
            return "Authorization code not received", 400

        client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
        client_secret = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
        if not client_id or not client_secret:
            current_app.logger.error("OAuth credentials not configured")
            return "OAuth credentials not configured", 500

        callback_url = get_callback_url()

        client = WebApplicationClient(client_id)
        google_provider_cfg = get_google_provider_cfg()
        token_endpoint = google_provider_cfg["token_endpoint"]

        # Ensure we're using HTTPS in the authorization response
        current_url = request.url
        if 'http://' in current_url:
            current_url = current_url.replace('http://', 'https://')

        token_url, headers, body = client.prepare_token_request(
            token_endpoint,
            authorization_response=current_url,
            redirect_url=callback_url,
            code=code
        )

        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(client_id, client_secret),
        )

        client.parse_request_body_response(json.dumps(token_response.json()))

        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)

        if not userinfo_response.ok:
            current_app.logger.error(f"Failed to get user info: {userinfo_response.text}")
            return "Failed to get user info", 500

        userinfo = userinfo_response.json()
        if not userinfo.get("email_verified"):
            return "User email not verified by Google.", 400

        users_email = userinfo["email"]
        users_name = userinfo.get("given_name", users_email.split("@")[0])

        from app import db
        from models import User

        user = User.query.filter_by(email=users_email).first()
        if not user:
            user = User(username=users_name, email=users_email)
            db.session.add(user)
            db.session.commit()

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