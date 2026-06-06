import gzip

def compress(data: bytes) -> bytes:
    return gzip.compress(data, compresslevel=9)

def decompress(data: bytes) -> bytes:
    return gzip.decompress(data)
