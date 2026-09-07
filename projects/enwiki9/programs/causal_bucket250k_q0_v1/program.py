"""Stable raw predecessor queues; use the published P/K/D gate for evidence."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import causal_bucket_v2 as codec

CANDIDATE_ID = 'causal_bucket250k_q0_v1'
SCOPE_BYTES = 250000
STAGE = 'development'
CONFIGURATION_COUNT = 1
NATIVE_PHASES = 9
OBJECTIVE_CREDIT_BYTES = 0


def compress(data):
    return codec.encode(data, mode="D", frame_size=65536)[0]


def decompress(archive):
    return codec.decode(archive)[0]
