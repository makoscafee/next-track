"""
Authentication endpoints for admin access.
"""

import os
from functools import wraps

from flask import request
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
    verify_jwt_in_request,
)
from flask_restful import Resource

# Admin credentials from environment (in production, use proper user management)
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "nexttrack_admin_2026")


def admin_required(fn):
    """Decorator to require admin authentication."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        identity = get_jwt_identity()
        if identity != ADMIN_USERNAME:
            return {"error": "Admin access required"}, 403
        return fn(*args, **kwargs)

    return wrapper


class AdminLoginResource(Resource):
    """Admin login endpoint."""

    def post(self):
        """
        Authenticate admin user and return JWT token.

        Body (JSON):
            username (required): Admin username
            password (required): Admin password

        Returns:
            200: JWT access token
            401: Invalid credentials
        """
        data = request.get_json() or {}

        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return {"error": "Username and password are required"}, 400

        if username != ADMIN_USERNAME or password != ADMIN_PASSWORD:
            return {"error": "Invalid credentials"}, 401

        access_token = create_access_token(identity=username)

        return {
            "status": "success",
            "access_token": access_token,
            "token_type": "Bearer",
        }, 200


class AdminVerifyResource(Resource):
    """Verify admin token is valid."""

    @admin_required
    def get(self):
        """
        Verify the current token is valid.

        Returns:
            200: Token is valid
            401: Invalid or expired token
        """
        identity = get_jwt_identity()
        return {
            "status": "valid",
            "username": identity,
        }, 200
