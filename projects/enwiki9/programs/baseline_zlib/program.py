import zlib

def compress(data: bytes) -> bytes:
    return zlib.compress(data, level=9)

def decompress(data: bytes) -> bytes:
    return zlib.decompress(data)
