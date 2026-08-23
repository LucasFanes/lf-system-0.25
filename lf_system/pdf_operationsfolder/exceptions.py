"""PDF domain exceptions."""


class PDFError(Exception):
    """Base exception for PDF module errors."""


class PDFNotOpenError(PDFError, RuntimeError):
    """Raised when an operation requires an open PDF."""


class PDFValidationError(PDFError, ValueError):
    """Raised when PDF operation input is invalid."""


class PDFPasswordError(PDFValidationError):
    """Raised when a PDF password operation cannot be completed."""


class PDFWriteError(PDFError, RuntimeError):
    """Raised when writing PDF bytes fails."""
