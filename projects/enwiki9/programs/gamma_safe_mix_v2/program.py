"""Infrastructure-only SAFE-MIX proof envelope; not a standalone codec."""


def compress(data: bytes) -> bytes:
    raise NotImplementedError("implement compress")


def decompress(archive: bytes) -> bytes:
    raise NotImplementedError("implement decompress")
