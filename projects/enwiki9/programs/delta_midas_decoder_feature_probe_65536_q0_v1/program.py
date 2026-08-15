"""Zero-credit marker for the prospective DELTA-MIDAS feature probe."""


EXPERIMENT = (
    "operations/adaptive/experiments/"
    "delta_midas_decoder_feature_probe_65536_q0_v1.json"
)
CLAIM_BOUNDARY = "causal-shadow-not-a-codec"


def compress(data: bytes) -> bytes:
    del data
    raise RuntimeError("DELTA-MIDAS feature prediction is not a compressor")


def decompress(archive: bytes) -> bytes:
    del archive
    raise RuntimeError("DELTA-MIDAS feature prediction is not a decompressor")
