from __future__ import annotations

import time
import tracemalloc
from typing import NamedTuple
tracemalloc.start()


class ProfileSnapshot(NamedTuple):
    wall_time_ms: float
    cpu_time_ms: float 
    memory_delta_kb: float
    memory_peak_kb: float  


class Profiler:
    """Context manager that captures wall time, CPU time, and heap usage."""

    __slots__ = (
        "_start_wall_time",
        "_start_cpu_time",
        "_memory_before_bytes",
        "snapshot",
    )

    def __init__(self) -> None:
        self._start_wall_time: float = 0.0
        self._start_cpu_time: float = 0.0
        self._memory_before_bytes: int = 0
        self.snapshot: ProfileSnapshot | None = None

    def __enter__(self) -> "Profiler":
        tracemalloc.reset_peak()
        self._memory_before_bytes = tracemalloc.get_traced_memory()[0]
        self._start_wall_time = time.perf_counter()
        self._start_cpu_time = time.process_time()
        return self

    def __exit__(self, *_) -> None:
        wall_time_ms = (time.perf_counter() - self._start_wall_time) * 1000.0
        cpu_time_ms = (time.process_time() - self._start_cpu_time) * 1000.0

        memory_current_bytes, memory_peak_bytes = tracemalloc.get_traced_memory()
        memory_delta_bytes = memory_current_bytes - self._memory_before_bytes

        self.snapshot = ProfileSnapshot(
            wall_time_ms=round(wall_time_ms, 2),
            cpu_time_ms=round(cpu_time_ms, 3),
            memory_delta_kb=round(memory_delta_bytes / 1024.0, 2),
            memory_peak_kb=round(memory_peak_bytes / 1024.0, 2),
        )
