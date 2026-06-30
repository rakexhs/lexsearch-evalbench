"""Lightweight timing utilities for per-stage latency measurement."""
from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Dict, Iterator


@dataclass
class Timer:
    """Accumulates named stage durations (milliseconds)."""

    stages: Dict[str, float] = field(default_factory=dict)

    @contextmanager
    def measure(self, name: str) -> Iterator[None]:
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            self.stages[name] = self.stages.get(name, 0.0) + elapsed_ms

    def total_ms(self) -> float:
        return sum(self.stages.values())

    def as_dict(self) -> Dict[str, float]:
        d = {k: round(v, 3) for k, v in self.stages.items()}
        d["total_ms"] = round(self.total_ms(), 3)
        return d


@contextmanager
def timed(sink: Dict[str, float], name: str) -> Iterator[None]:
    start = time.perf_counter()
    try:
        yield
    finally:
        sink[name] = round((time.perf_counter() - start) * 1000.0, 3)
