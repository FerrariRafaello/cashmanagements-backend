# IMPORTS
from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.exceptions import UserAlreadyExistsException, CredentialsException, InvalidTokenTypeException
from app.core.security import decode_token
from app.db.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, TokenResponse, UserUpdate, LoginRequest
from app.services.user import create_user, get_user_by_email, authenticate_user, update_user, deactivate_user, get_user_by_id
from app.core.security import create_access_token, create_refresh_token
from app.middleware.security import limiter

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=201)
@limiter.limit("5/minute")
def register(
    request: Request,
    user_data: UserCreate,
    db: Session = Depends(get_db)) -> UserResponse:
    """
    Registers a new user.
    Raises 409 if email is already in use.
    """
    existing = get_user_by_email(db, user_data.email)
    if existing:
        raise UserAlreadyExistsException()
    return create_user(db, user_data)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(
    request: Request,
    user_data: LoginRequest,
    db: Session = Depends(get_db)) -> TokenResponse:
    """
    Authenticates a user and return acess + refresh tokens.
    Raises 401 if credentials are invalid.
    """
    user = authenticate_user(db, user_data.email, user_data.password)
    if not user:
        raise CredentialsException()
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("5/minute")
def refresh_token(
    request: Request,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> TokenResponse:
    """
    Issues a new access token using a valid refresh token.
    Raises 401 if the token is invalid or not a refresh type.
    """
    payload = decode_token(token)
    
    if payload is None:
        raise CredentialsException()
    
    if payload.get("type") != "refresh":
        raise InvalidTokenTypeException()
    
    user_id = payload.get("sub")
    if not user_id:
        raise CredentialsException()

    user = get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise CredentialsException()

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """
    Returns the current authenticated user's data.
    Requires a valid acess token.
    """
    return current_user


@router.patch("/me", response_model=UserResponse)
@limiter.limit("10/minute")
def update_me(
    request: Request,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """Updates the current authenticated user's data."""
    return update_user(db, current_user.id, user_data)


@router.delete("/me", status_code=204)
@limiter.limit("5/minute")
def deactivate_me(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Soft deletes the currnt authenticated user.
    Sets is-active to False.
    """
    deactivate_user(db, current_user.id)
