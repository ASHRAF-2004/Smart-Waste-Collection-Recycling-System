"""Custom application exceptions."""


class AppError(Exception):
    """Base user-facing application error."""


class ValidationError(AppError):
    """Raised when user input validation fails."""


class AuthorizationError(AppError):
    """Raised when user is not authorized for an action."""


class NotFoundError(AppError):
    """Raised when an entity cannot be found."""


class DatabaseError(AppError):
    """Raised on handled database failures."""
