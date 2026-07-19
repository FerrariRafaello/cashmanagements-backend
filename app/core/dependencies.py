# IMPORTS
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.core.exceptions import CredentialsException, InvalidTokenTypeException, InactiveUserException
from app.db.database import get_db # still needs to be created
from app.models.user import User

# Tells FastAPI where the login endpoint is, used in Swagger UI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
) -> User:
    """
    Decodes the JWT access token from the request header.
    Returns the current authenticated user or raises 401.
    """
    payload = decode_token(token)

    if payload is None:
        raise CredentialsException()

    if payload.get("type") != "access":
        raise InvalidTokenTypeException()
    
    user_id: int = payload.get("sub")
    if user_id is None:
        raise CredentialsException()
    
    # Importing here to avoid circular imports
    from app.services.user import get_user_by_id
    user = get_user_by_id(db, int(user_id))

    if user is None:
        raise CredentialsException()
    
    if not user.is_active:
        raise InactiveUserException()

    return user
