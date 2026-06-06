import bz2

def compress(data: bytes) -> bytes:
    return bz2.compress(data, compresslevel=9)

def decompress(data: bytes) -> bytes:
    return bz2.decompress(data)
