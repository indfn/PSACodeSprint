"""Admin authentication — simple session-based auth for /admin endpoints.

Credentials: admin / admin123 (hardcoded for demo).
Session: signed cookie, 1-hour expiry.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import time
from functools import wraps
from typing import Any

from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse

# Credentials from env vars (demo defaults for local dev only)
_ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
_ADMIN_PASS = os.environ.get("ADMIN_PASS", "admin123")
_SESSION_SECRET = os.environ.get("ADMIN_SESSION_SECRET", "psa-nexus-admin-dev-secret")
_SESSION_TTL = 3600  # 1 hour


def _sign_session(user: str, expires: float) -> str:
    """HMAC-sign a session token."""
    payload = f"{user}:{expires}"
    sig = hmac.new(_SESSION_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()[:16]
    return f"{user}:{expires}:{sig}"


def _verify_session(token: str) -> str | None:
    """Verify session token. Returns username if valid, None if expired/invalid."""
    try:
        parts = token.split(":")
        if len(parts) != 3:
            return None
        user, expires_str, sig = parts
        expires = float(expires_str)
        if time.time() > expires:
            return None
        expected = hmac.new(_SESSION_SECRET.encode(), f"{user}:{expires}".encode(), hashlib.sha256).hexdigest()[:16]
        if not hmac.compare_digest(sig, expected):
            return None
        return user
    except Exception:
        return None


def create_session_cookie(username: str) -> str:
    """Create a signed session cookie value."""
    expires = time.time() + _SESSION_TTL
    return _sign_session(username, expires)


def check_auth(request: Request) -> str:
    """Check admin auth from request. Returns username or raises 401."""
    token = request.cookies.get("psa_admin_session")
    if not token:
        # Also check Authorization header (Bearer token)
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Admin login required. POST /api/admin/login")
    user = _verify_session(token)
    if not user:
        raise HTTPException(status_code=401, detail="Session expired or invalid. POST /api/admin/login")
    return user


def verify_credentials(username: str, password: str) -> bool:
    """Verify admin credentials."""
    return hmac.compare_digest(username, _ADMIN_USER) and hmac.compare_digest(password, _ADMIN_PASS)
