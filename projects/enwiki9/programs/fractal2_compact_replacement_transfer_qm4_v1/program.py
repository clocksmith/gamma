"""Manifest stub for the zero-credit compact FRACTAL-2 transfer gate."""


def compress(data: bytes) -> bytes:
    raise RuntimeError("QM4 is a trace-priced transfer gate, not a codec")


def decompress(archive: bytes) -> bytes:
    raise RuntimeError("QM4 has no constructive archive before paid replay")
