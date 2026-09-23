"""Qt-independent, throttled activity reporting for file operations."""
import time
from typing import BinaryIO, Callable

Progress = Callable[[str], None]


def ignore_progress(message: str) -> None:
    pass


class ProgressReader:
    """Report at most once per second, plus a final count, without buffering SQL."""

    def __init__(self, source: BinaryIO, total: int, progress: Progress,
                 label: str = "Read", interval: float = 1.0):
        self.source = source
        self.total = total
        self.progress = progress
        self.label = label
        self.interval = interval
        self.count = 0
        self.last_report = time.monotonic()
        self.finished = False

    def read(self, size: int = -1) -> bytes:
        data = self.source.read(size)
        self.count += len(data)
        now = time.monotonic()
        if not self.finished and (not data or now - self.last_report >= self.interval):
            self.progress(f"{self.label}: {self.count:,} / {self.total:,} bytes")
            self.last_report = now
        if not data:
            self.finished = True
        return data
