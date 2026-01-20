"""Progress callback protocol for decoupling business logic from UI."""

from typing import Callable, Protocol, runtime_checkable


@runtime_checkable
class ProgressCallback(Protocol):
    """Protocol for progress reporting callbacks.

    This allows business logic to report progress without being coupled
    to a specific UI implementation (CLI print, GUI status bar, etc.).
    """
    def __call__(self, message: str, level: str = "info") -> None:
        """Report progress.

        Args:
            message: The progress message to report.
            level: Message level - "info", "warning", "error", or "success".
        """
        ...


def print_progress(message: str, level: str = "info") -> None:
    """Default CLI progress callback - prints to stdout."""
    print(message)


def null_progress(message: str, level: str = "info") -> None:
    """Silent progress callback for testing or background operations."""
    pass


# Type alias for convenience
ProgressCallbackType = Callable[[str, str], None]
