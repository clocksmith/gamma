#!/usr/bin/env python3
"""Tests for the FX2-lite PPMD context-recovery sealer."""

from __future__ import annotations

import unittest

from projects.enwiki9.tools.seal_cmix21_lstm200_fx2lite428_context_recovery import (
    require_context_failure,
)


class ContextFailureTests(unittest.TestCase):
    def test_authorized_failure_is_accepted(self) -> None:
        require_context_failure(
            {
                "schema": "cmix21_lstm200_fx2lite428_context_restore_failure_v1",
                "decision": {"selective_context_restore_replay_authorized": True},
            }
        )

    def test_wrong_schema_is_rejected(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "unexpected"):
            require_context_failure({"schema": "wrong", "decision": {}})

    def test_missing_authorization_is_rejected(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "did not authorize"):
            require_context_failure(
                {
                    "schema": "cmix21_lstm200_fx2lite428_context_restore_failure_v1",
                    "decision": {},
                }
            )


if __name__ == "__main__":
    unittest.main()
