import copy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    "artifact_contract", Path(__file__).with_name("artifact_contract.py")
)
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)


def fixture():
    width = 2 * 1024**2
    return {
        f"model.layers.{layer}.mlp.ttt_proj.weight": {
            "dtype": "BF16",
            "shape": [1024, 1024],
            "data_offsets": [index * width, (index + 1) * width],
        }
        for index, layer in enumerate(contract.LAYERS)
    }


class ArtifactTests(unittest.TestCase):
    def test_complete_projection_set(self):
        contract.validate_projections(fixture(), 7 * 2 * 1024**2)

    def test_missing_single_projection_rejected(self):
        for key in fixture():
            header = fixture()
            del header[key]
            with self.assertRaises(ValueError):
                contract.validate_projections(header, 7 * 2 * 1024**2)

    def test_malformed_projection_rejected(self):
        for field, value in [
            ("dtype", "F32"),
            ("shape", [1024, 1]),
            ("data_offsets", [-1, 2 * 1024**2 - 1]),
            ("data_offsets", [False, 2 * 1024**2]),
            ("data_offsets", [0, 1]),
            ("data_offsets", [0]),
        ]:
            header = copy.deepcopy(fixture())
            header[next(iter(header))][field] = value
            with self.assertRaises(ValueError):
                contract.validate_projections(header, 7 * 2 * 1024**2)

    def test_truncation_and_overlap_rejected(self):
        with self.assertRaises(ValueError):
            contract.validate_projections(fixture(), 1)
        header = fixture()
        keys = list(header)
        header[keys[1]]["data_offsets"] = header[keys[0]]["data_offsets"]
        with self.assertRaises(ValueError):
            contract.validate_projections(header, 7 * 2 * 1024**2)


if __name__ == "__main__":
    unittest.main()
