"""Project-specific exceptions."""

from __future__ import annotations


class DocuMindError(Exception):
    """Base exception for documind."""


class InvalidInputError(DocuMindError):
    """Raised when the CLI input is invalid."""


class OutputConflictError(DocuMindError):
    """Raised when the output directory cannot be written safely."""
