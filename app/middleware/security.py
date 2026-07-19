# IMPORTS
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address


# Rate limiter instance - used as decorator on routes
limiter = Limiter(key_func=get_remote_address)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds security headers to every response.
    Protects against XSS, clickjacking, MIME sniffing, and more.
    """
    async def dispatch(self, request: Request, call_next) -> JSONResponse:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        return response


class HoneypotMiddleware(BaseHTTPMiddleware):
    """
    Block common attack paths used by bots and scanners.
    Any request to these paths gets a 404 immediately.
    """
    HONEYPOT_PATHS = {
        "/admin", "/wp-admin", "/phpmyadmin",
        "/.env", "/config", "/setup", "/install"
    }

    async def dispatch(self, request: Request, call_next) -> JSONResponse:
        if request.url.path in self.HONEYPOT_PATHS:
            return JSONResponse(status_code=404, content={"detail": "Not found."})
        return await call_next(request)


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Rejects requests with a body larger than 1MB.
    Prevents memory exhaustion attacks.
    """
    MAX_BODY_SIZE = 1024 * 1024 # 1MB

    async def dispatch(self, request: Request, call_next) -> JSONResponse:
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.MAX_BODY_SIZE:
            return JSONResponse(
                status_code=413,
                content={"detail": "Request body too large."}
            )
        return await call_next(request)
