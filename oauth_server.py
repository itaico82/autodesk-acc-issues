#!/usr/bin/env python
"""
OAuth server for Autodesk Construction Cloud API authentication.
"""
import os
import secrets
import time
import uuid
import json
from typing import Dict, Optional, Any

from fastapi import FastAPI, Request, Response, Cookie
from fastapi.responses import RedirectResponse
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get credentials
AUTODESK_CLIENT_ID = os.environ.get("AUTODESK_CLIENT_ID")
AUTODESK_CLIENT_SECRET = os.environ.get("AUTODESK_CLIENT_SECRET")
REDIRECT_URI = "http://127.0.0.1:8000/oauth/callback"

if not AUTODESK_CLIENT_ID or not AUTODESK_CLIENT_SECRET:
    raise ValueError("AUTODESK_CLIENT_ID and AUTODESK_CLIENT_SECRET must be set in .env file")

print(f"Using Client ID: {AUTODESK_CLIENT_ID[:5]}... (truncated)")
print(f"Redirect URI: {REDIRECT_URI}")

# OAuth endpoints
AUTH_URL = "https://developer.api.autodesk.com/authentication/v2/authorize"
TOKEN_URL = "https://developer.api.autodesk.com/authentication/v2/token"

# Required scopes
SCOPES = "data:read data:write account:read account:write user:read user:write"

# Session storage
SESSIONS_FILE = "sessions.json"

def load_sessions() -> Dict[str, Any]:
    """Load sessions from file."""
    if os.path.exists(SESSIONS_FILE):
        try:
            with open(SESSIONS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading sessions: {e}")
    return {}

def save_sessions(sessions: Dict[str, Any]) -> None:
    """Save sessions to file."""
    try:
        with open(SESSIONS_FILE, 'w') as f:
            json.dump(sessions, f, indent=2)
    except Exception as e:
        print(f"Error saving sessions: {e}")

# Initialize FastAPI app
app = FastAPI()

# State tokens for CSRF protection
state_tokens: Dict[str, float] = {}

@app.get("/")
async def home():
    """Home page."""
    return "Autodesk Construction Cloud OAuth Server"

@app.get("/login")
async def login():
    """Initiate OAuth flow."""
    # Generate state token
    state = secrets.token_urlsafe(32)
    state_tokens[state] = time.time()
    
    # Clean up old state tokens
    current_time = time.time()
    expired_states = [s for s, t in state_tokens.items() if current_time - t > 3600]
    for state in expired_states:
        state_tokens.pop(state)
    
    # Build authorization URL
    params = {
        "client_id": AUTODESK_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "state": state
    }
    
    auth_url = f"{AUTH_URL}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
    print(f"Redirecting to: {auth_url}")
    
    return RedirectResponse(url=auth_url)

@app.get("/oauth/callback")
async def oauth_callback(code: str, state: str, response: Response):
    """Handle OAuth callback."""
    print(f"Received callback with code: {code[:5]}... and state: {state[:5]}...")
    
    # Verify state token
    if state not in state_tokens:
        return {"error": "Invalid state token"}
    
    # Remove used state token
    state_tokens.pop(state)
    
    # Exchange code for token
    print("Exchanging code for token...")
    token_data = {
        "client_id": AUTODESK_CLIENT_ID,
        "client_secret": AUTODESK_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI
    }
    
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            TOKEN_URL,
            data=token_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
    
    print(f"Token response status: {token_response.status_code}")
    
    if token_response.status_code != 200:
        return {"error": "Failed to obtain token", "details": token_response.text}
    
    print("Successfully obtained token")
    token_data = token_response.json()
    
    # Create session
    session_id = str(uuid.uuid4())
    session = {
        "access_token": token_data["access_token"],
        "scope": token_data.get("scope", SCOPES),
        "created_at": time.time(),
        "expires_at": time.time() + token_data.get("expires_in", 3600)
    }
    
    # Load existing sessions
    sessions = load_sessions()
    
    # Add new session
    sessions[session_id] = session
    print(f"Created session {session_id} with token")
    print(f"Active sessions: {list(sessions.keys())}")
    
    # Save sessions
    save_sessions(sessions)
    
    # Set session cookie
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        max_age=3600,
        samesite="lax"
    )
    
    # Redirect to dashboard
    return RedirectResponse(url="/dashboard")

@app.get("/dashboard")
async def dashboard(session_id: Optional[str] = Cookie(None)):
    """Dashboard page."""
    if not session_id:
        return RedirectResponse(url="/")
    
    sessions = load_sessions()
    if session_id not in sessions:
        return RedirectResponse(url="/")
    
    # Redirect to home for now
    return RedirectResponse(url="/")