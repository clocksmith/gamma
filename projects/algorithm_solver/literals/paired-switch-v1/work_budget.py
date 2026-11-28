"""One elapsed-time allowance for a search arm on a fixed device."""

from __future__ import annotations

import math
import time
from collections.abc import Callable


class OutOfBudget(Exception):
    """The next operation cannot be admitted, or its result arrived late."""


def positive_nanoseconds(seconds: float) -> int:
    if not math.isfinite(seconds) or seconds <= 0:
        raise ValueError("a budget or verifier timeout must be finite and positive")
    return math.ceil(seconds * 1_000_000_000)


class ArmBudget:
    def __init__(
        self,
        limit_ns: int,
        *,
        shared_setup_ns: int = 0,
        synchronize: Callable[[], None],
        clock: Callable[[], int] = time.perf_counter_ns,
    ) -> None:
        self.limit_ns = limit_ns
        self.synchronize = synchronize
        self.clock = clock
        self.phase_ns = {"shared_setup": shared_setup_ns, "setup": 0, "generation": 0, "verification": 0}
        self.phase = "setup"
        self.phase_start = self.clock()
        self.deadline = self.phase_start + limit_ns - shared_setup_ns

    def _boundary(self) -> int:
        self.synchronize()
        now = self.clock()
        self.phase_ns[self.phase] = self.phase_ns.get(self.phase, 0) + now - self.phase_start
        self.phase_start = now
        return now

    def enter(self, phase: str, reserve_ns: int = 1) -> None:
        now = self._boundary()
        self.phase = phase
        if self.deadline - now < reserve_ns:
            raise OutOfBudget(phase)

    def checkpoint(self) -> None:
        self.synchronize()
        if self.clock() >= self.deadline:
            raise OutOfBudget(self.phase)

    def finish(self) -> int:
        """Charge the final phase, including device completion and verifier teardown."""
        self._boundary()
        return sum(self.phase_ns.values())
