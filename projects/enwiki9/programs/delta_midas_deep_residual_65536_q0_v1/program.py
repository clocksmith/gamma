"""Zero-credit marker for the frozen DELTA-MIDAS residual experiment."""


EXPERIMENT = (
    "operations/adaptive/experiments/"
    "delta_midas_deep_residual_65536_q0_v1.json"
)
CLAIM_BOUNDARY = "causal-shadow-not-a-codec"


def compress(data: bytes) -> bytes:
    del data
    raise RuntimeError("DELTA-MIDAS residual attribution is not a compressor")


def decompress(archive: bytes) -> bytes:
    del archive
    raise RuntimeError("DELTA-MIDAS residual attribution is not a decompressor")
