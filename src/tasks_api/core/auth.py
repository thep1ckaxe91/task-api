from datetime import datetime, timezone, timedelta
from functools import wraps
from typing import Any, Callable, Dict, Optional
import jwt
from flask import current_app, g, request

from tasks_api.core.errors import ProblemException


def generate_token(
    user_id: str,
    secret_key: Optional[str] = None,
    algorithm: Optional[str] = None,
    expires_in_seconds: int = 3600,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate a standard RFC 7519 JWT for testing and development.
    https://datatracker.ietf.org/doc/html/rfc7519
    """
    secret = secret_key or current_app.config.get("JWT_SECRET_KEY", "dev-jwt-secret-key-change-in-production")
    algo = algorithm or current_app.config.get("JWT_ALGORITHM", "HS256")
    now = datetime.now(timezone.utc)

    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + timedelta(seconds=expires_in_seconds),
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, secret, algorithm=algo)


def require_jwt_auth(fn: Callable) -> Callable:
    """
    Decorator to protect endpoints with Bearer JWT authentication.
    Extracts claims and populates g.current_user and g.jwt_claims.
    Raises RFC 7807 ProblemException(401) on failure.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise ProblemException(
                status=401,
                title="Unauthorized",
                detail="Missing Authorization header with Bearer token.",
            )

        parts = auth_header.strip().split(" ")
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise ProblemException(
                status=401,
                title="Unauthorized",
                detail="Invalid Authorization header format. Expected 'Bearer <token>'.",
            )

        token = parts[1]
        secret = current_app.config.get("JWT_SECRET_KEY")
        algo = current_app.config.get("JWT_ALGORITHM", "HS256")

        try:
            payload = jwt.decode(
                token,
                secret,
                algorithms=[algo],
                options={"require": ["exp", "sub"]},
            )
        except jwt.ExpiredSignatureError:
            raise ProblemException(
                status=401,
                title="Unauthorized",
                detail="Token signature has expired.",
            )
        except jwt.InvalidTokenError as exc:
            raise ProblemException(
                status=401,
                title="Unauthorized",
                detail=f"Invalid token: {str(exc)}",
            )

        # Store authenticated identity in application context
        g.current_user = payload.get("sub")
        g.jwt_claims = payload

        return fn(*args, **kwargs)

    return wrapper
