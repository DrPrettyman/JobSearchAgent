"""Services layer for JobSearch application.

This module provides business logic services that can be used by any UI
(CLI, GUI, API, etc.) without being coupled to a specific implementation.
"""

from .progress import (
    ProgressCallback,
    ProgressCallbackType,
    print_progress,
    null_progress,
)
from .cover_letter_service import CoverLetterService, CoverLetterResult
from .user_profile_service import UserProfileService, ServiceResult

__all__ = [
    # Progress callbacks
    "ProgressCallback",
    "ProgressCallbackType",
    "print_progress",
    "null_progress",
    # Services
    "CoverLetterService",
    "CoverLetterResult",
    "UserProfileService",
    "ServiceResult",
]
