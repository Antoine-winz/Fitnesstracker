import json
import os
import requests
from flask import Blueprint, redirect, request, url_for
from flask_login import login_required, login_user, logout_user
from oauthlib.oauth2 import WebApplicationClient

# Import models and db after blueprint creation to avoid circular imports
google_auth = Blueprint("google_auth", __name__)

GOOGLE_CLIENT_ID = os.environ["GOOGLE_OAUTH_CLIENT_ID"]
GOOGLE_CLIENT_SECRET = os.environ["GOOGLE_OAUTH_CLIENT_SECRET"]
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

client = WebApplicationClient(GOOGLE_CLIENT_ID)

# Print setup instructions
print(f"""To make Google authentication work:
1. Go to https://console.cloud.google.com/apis/credentials
2. Create a new OAuth 2.0 Client ID
3. Add https://{os.environ.get('REPLIT_DEV_DOMAIN')}/google_login/callback to Authorized redirect URIs""")

@google_auth.route("/google_login")
def login():
    google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]
    
    # Construct the callback URL using the REPLIT_DEV_DOMAIN
    callback_url = f"https://{os.environ.get('REPLIT_DEV_DOMAIN')}/google_login/callback"
    
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=callback_url,
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)

@google_auth.route("/google_login/callback")
def callback():
    # Import here to avoid circular imports
    from app import db
    from models import User

    code = request.args.get("code")
    google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
    token_endpoint = google_provider_cfg["token_endpoint"]
    
    # Use the same callback URL as in the login route
    callback_url = f"https://{os.environ.get('REPLIT_DEV_DOMAIN')}/google_login/callback"

    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url.replace("http://", "https://"),
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

@google_auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))
