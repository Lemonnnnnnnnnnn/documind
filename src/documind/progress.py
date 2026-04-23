"""Minimal progress reporting utilities."""

from __future__ import annotations

from contextlib import contextmanager
from time import perf_counter


class ProgressReporter:
    def __init__(self, emit) -> None:
        self.emit = emit

    @contextmanager
    def stage(self, label: str):
        self.emit(f"{label}...")
        started = perf_counter()
        try:
            yield
        finally:
            elapsed = perf_counter() - started
            self.emit(f"{label} done ({elapsed:.2f}s)")
