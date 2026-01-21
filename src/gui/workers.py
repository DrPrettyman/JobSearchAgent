"""Background worker threads for async operations."""

from typing import Callable, Any
from PySide6.QtCore import QThread, Signal


class Worker(QThread):
    """Generic worker thread for running functions in the background.

    Usage:
        worker = Worker(some_function, arg1, arg2, kwarg1=value)
        worker.progress.connect(handle_progress)
        worker.finished.connect(handle_result)
        worker.start()
    """
    finished = Signal(object)
    progress = Signal(str, str)  # message, level
    error = Signal(str)

    def __init__(self, fn: Callable, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self._is_cancelled = False

    def run(self):
        try:
            # Inject progress callback if the function accepts it
            self.kwargs['on_progress'] = self._emit_progress
            result = self.fn(*self.args, **self.kwargs)
            if not self._is_cancelled:
                self.finished.emit(result)
        except TypeError:
            # Function doesn't accept on_progress, try without it
            try:
                del self.kwargs['on_progress']
                result = self.fn(*self.args, **self.kwargs)
                if not self._is_cancelled:
                    self.finished.emit(result)
            except Exception as e:
                if not self._is_cancelled:
                    self.error.emit(str(e))
        except Exception as e:
            if not self._is_cancelled:
                self.error.emit(str(e))

    def _emit_progress(self, message: str, level: str = "info"):
        """Progress callback that emits signal."""
        if not self._is_cancelled:
            self.progress.emit(message, level)

    def cancel(self):
        """Request cancellation of the worker."""
        self._is_cancelled = True


class ServiceWorker(QThread):
    """Worker specifically for service methods that return ServiceResult.

    Handles the common pattern of services returning result objects.
    """
    finished = Signal(object)  # ServiceResult or similar
    progress = Signal(str, str)
    error = Signal(str)

    def __init__(self, service_method: Callable, *args, **kwargs):
        super().__init__()
        self.service_method = service_method
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.service_method(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
