"""Read-only qualification of the pinned candidate; never download or execute it."""

import argparse
import hashlib
import json
from pathlib import Path
import struct

REVISION = "786708b3d940e139edf60a62995f5b2c5a8059a4"
WEIGHT_SHA256 = "bbd600491d2c5dff5fc73d429fb5b4f62e5bde9777f72ed31c09eae01798bc4e"
WEIGHT_BYTES = 1_517_981_192
LAYERS = (0, 4, 8, 12, 16, 20, 24)


def validate_projections(header, data_bytes):
    """Require every trained projection; identity fallback is not acceptable."""
    spans = []
    for layer in LAYERS:
        key = f"model.layers.{layer}.mlp.ttt_proj.weight"
        tensor = header.get(key)
        if not isinstance(tensor, dict):
            raise ValueError(f"Missing trained projection: {key}")
        if tensor.get("dtype") != "BF16" or tensor.get("shape") != [1024, 1024]:
            raise ValueError(f"Wrong projection dtype/shape: {key}")
        offsets = tensor.get("data_offsets")
        if not isinstance(offsets, list) or len(offsets) != 2:
            raise ValueError(f"Invalid projection offsets: {key}")
        start, end = offsets
        if any(type(value) is not int for value in offsets):
            raise ValueError(f"Noninteger projection offsets: {key}")
        if not 0 <= start < end <= data_bytes or end - start != 2 * 1024**2:
            raise ValueError(f"Truncated or malformed projection: {key}")
        spans.append((start, end))
    ordered = sorted(spans)
    if any(a[1] > b[0] for a, b in zip(ordered, ordered[1:])):
        raise ValueError("Overlapping projection tensors")


def qualify(directory):
    path = Path(directory) / "model.safetensors"
    if path.stat().st_size != WEIGHT_BYTES:
        raise ValueError("Candidate weight size does not match pinned artifact")
    with path.open("rb") as stream:
        raw = stream.read(8)
        if len(raw) != 8:
            raise ValueError("Truncated safetensors prefix")
        size = struct.unpack("<Q", raw)[0]
        if not 2 <= size <= 2_000_000:
            raise ValueError("Invalid or unexpectedly large safetensors header")
        header = json.loads(stream.read(size))
        validate_projections(header, WEIGHT_BYTES - 8 - size)
        stream.seek(0)
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if digest != WEIGHT_SHA256:
        raise ValueError("Candidate weight SHA-256 mismatch")
    config = json.loads((Path(directory) / "config.json").read_text())
    expected = {
        "hidden_size": 1024,
        "intermediate_size": 3072,
        "num_hidden_layers": 28,
        "ttt_layers": list(LAYERS),
        "ttt_proj": True,
    }
    for key, value in expected.items():
        if config.get(key) != value:
            raise ValueError(f"Candidate configuration mismatch: {key}")
    return {
        "revision": REVISION,
        "weight_sha256": digest,
        "trained_projection_count": len(LAYERS),
        "claim": "artifact identity and projection presence, not training provenance or quality",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    print(json.dumps(qualify(parser.parse_args().directory), indent=2))
