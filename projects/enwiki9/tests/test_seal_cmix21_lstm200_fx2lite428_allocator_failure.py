import unittest

from projects.enwiki9.tools.seal_cmix21_lstm200_fx2lite428_allocator_failure import (
    require_allocator_mapping,
)


class AllocatorMappingTest(unittest.TestCase):
    def test_accepts_complete_inlined_allocator_chain(self) -> None:
        require_allocator_mapping(
            "Fx2LitePPMD::ppmd_Model::remove(Fx2LitePPMD::ppmd_Model::BLK_NODE*)\n"
            "(inlined by) Fx2LitePPMD::ppmd_Model::AllocUnits(unsigned int)\n"
            "(inlined by) Fx2LitePPMD::ppmd_Model::UpdateModel("
            "Fx2LitePPMD::ppmd_Model::PPM_CONTEXT*)"
        )

    def test_rejects_downstream_only_mapping(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "misses allocator chain"):
            require_allocator_mapping(
                "Fx2LitePPMD::ppmd_Model::UpdateModel("
                "Fx2LitePPMD::ppmd_Model::PPM_CONTEXT*)"
            )


if __name__ == "__main__":
    unittest.main()
