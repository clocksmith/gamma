"""Helpers for counting and logging degraded-path fallbacks."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class FallbackTelemetry:
    """Track fallback reasons with structured logging."""

    namespace: str
    logger: logging.Logger
    counts: Dict[str, int] = field(default_factory=dict)

    def record(
        self,
        reason: str,
        exc: BaseException | None = None,
        *,
        level: int = logging.DEBUG,
        note: str = "",
    ) -> int:
        count = int(self.counts.get(reason, 0)) + 1
        self.counts[reason] = count
        if exc is None:
            if note:
                self.logger.log(
                    level,
                    "%s fallback '%s' (count=%d): %s",
                    self.namespace,
                    reason,
                    count,
                    note,
                )
            else:
                self.logger.log(
                    level,
                    "%s fallback '%s' (count=%d)",
                    self.namespace,
                    reason,
                    count,
                )
        else:
            self.logger.log(
                level,
                "%s fallback '%s' (count=%d): %s: %s",
                self.namespace,
                reason,
                count,
                type(exc).__name__,
                exc,
            )
        return count

    def snapshot(self) -> Dict[str, int]:
        return dict(self.counts)
