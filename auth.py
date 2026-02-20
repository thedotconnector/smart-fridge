"""Simple token-based auth for API routes."""

import os
import secrets
from functools import wraps

from flask import request, jsonify

# Pre-shared secrets (users exchange these for bearer tokens)
API_SECRET_1 = os.environ.get("API_SECRET_1", "")
API_SECRET_2 = os.environ.get("API_SECRET_2", "")

# Bearer tokens
API_TOKEN_1 = os.environ.get("API_TOKEN_1", "")
API_TOKEN_2 = os.environ.get("API_TOKEN_2", "")

_SECRETS = {API_SECRET_1, API_SECRET_2} - {""}
_TOKENS = {API_TOKEN_1, API_TOKEN_2} - {""}


def exchange_secret(secret):
    """Exchange a pre-shared secret for a bearer token. Returns token or None."""
    if secret == API_SECRET_1 and API_TOKEN_1:
        return API_TOKEN_1
    if secret == API_SECRET_2 and API_TOKEN_2:
        return API_TOKEN_2
    return None


def require_auth(f):
    """Decorator that checks for a valid Bearer token on API routes."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401
        token = auth_header[7:]
        if token not in _TOKENS:
            return jsonify({"error": "Invalid token"}), 401
        return f(*args, **kwargs)
    return decorated
