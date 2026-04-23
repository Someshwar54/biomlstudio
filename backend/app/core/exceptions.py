"""
Custom exceptions for the BioMLStudio application.
"""

class BioMLException(Exception):
    """Base exception for all application-specific exceptions."""
    def __init__(self, message: str, status_code: int = 400, **kwargs):
        self.message = message
        self.status_code = status_code
        self.extra = kwargs
        super().__init__(self.message)


class NotFoundException(BioMLException):
    """Raised when a requested resource is not found."""
    def __init__(self, resource: str, **kwargs):
        super().__init__(
            message=f"{resource} not found",
            status_code=404,
            **kwargs
        )


class UnauthorizedException(BioMLException):
    """Raised when a user is not authorized to access a resource."""
    def __init__(self, message: str = "Not authorized", **kwargs):
        super().__init__(
            message=message,
            status_code=401,
            **kwargs
        )


class ValidationException(BioMLException):
    """Raised when input validation fails."""
    def __init__(self, message: str = "Validation error", **kwargs):
        super().__init__(
            message=message,
            status_code=422,
            **kwargs
        )


class StorageException(BioMLException):
    """Raised when there's an error with file storage operations."""
    def __init__(self, message: str = "Storage error", **kwargs):
        super().__init__(
            message=message,
            status_code=500,
            **kwargs
        )


class ProcessingException(BioMLException):
    """Raised when there's an error during data processing."""
    def __init__(self, message: str = "Processing error", **kwargs):
        super().__init__(
            message=message,
            status_code=500,
            **kwargs
        )
