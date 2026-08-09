"""Diagnostic candidate wrapper for the KAIROS-108 observer gate."""


def compress(data: bytes) -> bytes:
    raise NotImplementedError("KAIROS opening observer is not a submission codec")


def decompress(archive: bytes) -> bytes:
    raise NotImplementedError("KAIROS opening observer is not a submission codec")
