#!/usr/bin/env python3
"""Tests for the strict exact-10M endpoint428 receipt sealer."""

from __future__ import annotations

import unittest

from projects.enwiki9.tools.seal_cmix21_lstm200_fx2lite428_10m import (
    recovery_wrapper_key,
)


class RecoveryWrapperKeyTests(unittest.TestCase):
    def test_direct_wrapper_recovery_schemas(self) -> None:
        for schema in (
            "cmix21_lstm200_fx2lite428_ram_recovery_v1",
            "cmix21_lstm200_fx2lite428_stats_recovery_v1",
            "cmix21_lstm200_fx2lite428_allocator_recovery_v1",
            "cmix21_lstm200_fx2lite428_context_recovery_v1",
        ):
            with self.subTest(schema=schema):
                self.assertEqual(recovery_wrapper_key(schema), "wrapper")

    def test_ppmd_recovery_uses_repair_wrapper(self) -> None:
        self.assertEqual(
            recovery_wrapper_key("cmix21_lstm200_fx2lite428_ppmd_recovery_v1"),
            "repair_wrapper",
        )

    def test_unknown_schema_is_rejected(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "unexpected recovery receipt schema"):
            recovery_wrapper_key("unknown")


if __name__ == "__main__":
    unittest.main()
