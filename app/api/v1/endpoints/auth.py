# IMPORTS
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.exceptions import UserAlreadyExistsException, CredentialsException
from app.db.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, TokenResponse, UserUpdate
from app.services.user import create_user, get_user_by_email, authenticate_user, update_user, deactivate_user
from app.core.security import create_access_token, create_refresh_token

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=201)
def register(user_data: UserCreate, db: Session = Depends(get_db)) -> UserResponse:
    """
    Registers a new user.
    Raises 409 if email is already in use.
    """
    existing = get_user_by_email(db, user_data.email)
    if existing:
        raise UserAlreadyExistsException()
    return create_user(db, user_data)


@router.post("/login", response_model=TokenResponse)
def login(user_data: UserCreate, db: Session = Depends(get_db)) -> TokenResponse:
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


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """
    Returns the current authenticated user's data.
    Requires a valid acess token.
    """
    return current_user


@router.patch("/me", response_model=UserResponse)
def update_me(
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """Updates the current authenticated user's data."""
    return update_user(db, current_user.id, user_data)


@router.delete("/me", status_code=204)
def deactivate_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Soft deletes the currnt authenticated user.
    Sets is-active to False.
    """
    deactivate_user(db, current_user.id)
