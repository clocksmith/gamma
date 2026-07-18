from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


TOOL = (
    Path(__file__).resolve().parents[1]
    / "projects/enwiki9/tools/run_fx2_cmix21_wrapper_proof.py"
)


def load_tool():
    spec = spec_from_file_location("run_lstm112_plus80_wrapper_proof", TOOL)
    module = module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_framed_payload_identity(tmp_path):
    tool = load_tool()
    payload = tmp_path / "payload"
    framed = tmp_path / "framed"
    payload.write_bytes(b"archive")
    framed.write_bytes(b"Garchive")
    assert tool.framed_payload_identical(framed, payload) == (b"G", True)


def test_framed_payload_rejects_mismatch(tmp_path):
    tool = load_tool()
    payload = tmp_path / "payload"
    framed = tmp_path / "framed"
    payload.write_bytes(b"archive")
    framed.write_bytes(b"Garchivf")
    assert tool.framed_payload_identical(framed, payload) == (b"G", False)
