from google.oauth2 import id_token
from google.auth.transport import requests
import os
from dotenv import load_dotenv
load_dotenv('.env.local')

def verify_google_token(token: str):
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    if not GOOGLE_CLIENT_ID:
        raise Exception("GOOGLE_CLIENT_ID not configured")
    
    idinfo = id_token.verify_oauth2_token(
        token,
        requests.Request(),
        GOOGLE_CLIENT_ID
    )

    if not idinfo.get("email_verified"):
        raise Exception("Email not verified")

    return {
        "email": idinfo["email"],
        "name": idinfo.get("name"),
        "picture": idinfo.get("picture"),
        "google_id": idinfo["sub"]
    }
