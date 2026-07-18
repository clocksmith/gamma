#!/usr/bin/env python3
"""Tests for the FX2-lite PPMD context-restore failure sealer."""

from __future__ import annotations

import unittest

from projects.enwiki9.tools.seal_cmix21_lstm200_fx2lite428_context_restore_failure import (
    require_restore_mapping,
)


class RestoreMappingTests(unittest.TestCase):
    def test_complete_mapping_is_accepted(self) -> None:
        require_restore_mapping(
            "Fx2LitePPMD::ppmd_Model::RestoreModelRare\n"
            "Fx2LitePPMD::ppmd_Model::ppmd_UpdateByte"
        )

    def test_missing_restore_function_is_rejected(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "RestoreModelRare"):
            require_restore_mapping("Fx2LitePPMD::ppmd_Model::ppmd_UpdateByte")

    def test_missing_caller_is_rejected(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "ppmd_UpdateByte"):
            require_restore_mapping("Fx2LitePPMD::ppmd_Model::RestoreModelRare")


if __name__ == "__main__":
    unittest.main()
