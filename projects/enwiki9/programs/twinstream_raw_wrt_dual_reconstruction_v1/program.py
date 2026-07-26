"""Manifest entry for the D02 TWINSTREAM causal-shadow experiment.

The executable experiment is ``tools/wrt_twinstream_shadow.py``. This program
is intentionally not queueable as a constructive compressor: the first gate
uses external, hash-pinned WRT artifacts to attribute P0/P1/P2/P3/PX and earns
zero score credit.
"""


def compress(data: bytes) -> bytes:
    raise RuntimeError("D02 is a causal shadow until its frozen transfer gate passes")


def decompress(archive: bytes) -> bytes:
    raise RuntimeError("D02 has no constructive archive at the shadow stage")
