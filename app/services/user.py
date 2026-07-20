# IMPORTS
from sqlalchemy.orm import Session
from uuid import UUID

from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import hash_password, verify_password
from app.core.exceptions import UserAlreadyExistsException
from app.schemas.user import UserCreate, UserUpdate


def get_user_by_id(db: Session, user_id: UUID) -> User | None:
    """Fetches a user by their UUID."""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> User | None:
    """Fetches a user by their email address."""
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, user_data: UserCreate) -> User:
    """
    Creates a new user in the database.
    Hashes the password before storing.
    """
    hashed = hash_password(user_data.password)
    db_user = User(
        name=user_data.name,
        email=user_data.email,
        hashed_password=hashed,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, user_id: UUID, user_data: "UserUpdate") -> User | None:
    """
    Updates user fields (name, email, password).
    Only updates fields that were actually provided.
    Raises 409 if the new email is already in use by another user.
    """
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    if user_data.name:
        user.name = user_data.name.strip()
    if user_data.email:
        existing = get_user_by_email(db, user_data.email)
        if existing and existing.id != user_id:
            raise UserAlreadyExistsException()
        user.email = user_data.email.strip().lower()
    if user_data.password:
        user.hashed_password = hash_password(user_data.password)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """
    Validates email and password.
    Returns the user if valid, None if not.
    """
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
    return user


def deactivate_user(db: Session, user_id: UUID) -> User | None:
    """ Soft deletes a user by setting is_active to False."""
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    user.is_active = False
    db.commit()
    db.refresh(user)
    return user
