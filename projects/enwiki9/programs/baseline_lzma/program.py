import lzma

PRESET = 9 | lzma.PRESET_EXTREME

def compress(data: bytes) -> bytes:
    return lzma.compress(data, preset=PRESET)

def decompress(data: bytes) -> bytes:
    return lzma.decompress(data)
