# IMPORTS
from fastapi import HTTPException, status

class CredentialsException(HTTPException):
    """Raised when JWT token is invalid or expired."""
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validade credentials.",
            headers={"WWW_Authenticate": "Bearer"},
        )


class UserNotFoundException(HTTPException):
    """Raised when the user is not found in the datadbase."""
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )


class UserAlreadyExistsException(HTTPException):
    """Raised when trying to register with an email already in use."""
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered.",
        )


class InvalidTokenTypeException(HTTPException):
    """Raised when the wrong token is used (e.g. refresh token used as access)."""
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid token type.",
            headers={"WWW-Authenticate": "Bearer"},
        )


class InactivateUserException(HTTPException):
    """Raised when a deactivated user tries to log in."""
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user.",
        )
