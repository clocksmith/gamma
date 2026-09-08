"""Fixed opcode field repair; D is the submission default."""
import importlib.util
from pathlib import Path

_root = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("opcode_field_codec", _root / "field_codec.py")
_codec = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_codec)


def compress(data):
    return _codec.encode(data, candidate_root=_root)[0]


def decompress(data):
    return _codec.decode(data, candidate_root=_root)[0]
