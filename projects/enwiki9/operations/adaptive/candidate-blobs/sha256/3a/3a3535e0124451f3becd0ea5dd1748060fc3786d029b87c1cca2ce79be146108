"""Fixed raw block direction; use the published P/K/D gate for evidence."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import raw_reverse_bz2_v1 as codec

CANDIDATE_ID = 'raw_reverse_bz2250k_q0_v1'
SCOPE_BYTES = 250000
STAGE = 'development'
CONFIGURATION_COUNT = 1
NATIVE_PHASES = 9
OBJECTIVE_CREDIT_BYTES = 0


def compress(data):
    return codec.encode(data, mode="D", block_size=250000)[0]


def decompress(archive):
    return codec.decode(archive)[0]
