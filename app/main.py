# IMPORTS
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.middleware.security import (
    SecurityHeadersMiddleware,
    HoneypotMiddleware,
    RequestSizeLimitMiddleware,
    limiter,
)
from app.api.v1.endpoints import auth


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Middleware - order matters, first added is last executed
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(HoneypotMiddleware)
app.add_middleware(RequestSizeLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allor_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])


@app.get("/health", tags=["health"])
def health_check() -> dict:
    """Returns PI status - used by Railway to verify the app is running."""
    return {"status": "ok", "version": settings.APP_VERSION}
