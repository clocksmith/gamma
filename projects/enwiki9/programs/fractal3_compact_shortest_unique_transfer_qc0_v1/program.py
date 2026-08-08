"""Manifest stub for the zero-credit compact causal transfer gate."""


def compress(data: bytes) -> bytes:
    raise RuntimeError("QC0 is a trace-priced transfer gate, not a codec")


def decompress(archive: bytes) -> bytes:
    raise RuntimeError("QC0 has no constructive archive before paid replay")
