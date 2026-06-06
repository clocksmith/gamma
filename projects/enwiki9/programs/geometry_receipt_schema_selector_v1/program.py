import lzma, os

_D = os.path.dirname(__file__)

def _load(name, fmt, filters=None):
    with open(os.path.join(_D, name), "rb") as f:
        src = lzma.decompress(f.read(), format=fmt, filters=filters)
    ns = {}
    exec(src, ns)
    return ns

_G = _load("g", lzma.FORMAT_RAW, [{"id": lzma.FILTER_LZMA2}])
_R = _load("r", lzma.FORMAT_ALONE)
_S = _load("s", lzma.FORMAT_ALONE)
_ST = {}

def _try(tag, mod, data, out):
    c = mod["compress"](data)
    out.append((len(c), tag + c))

def compress(data):
    global _ST
    n = len(data)
    out = []
    if n <= 50_000_000:
        _try(b"R", _R, data, out)
        _try(b"G", _G, data, out)
    else:
        _try(b"G", _G, data, out)
        _try(b"S", _S, data, out)
    _, best = min(out, key=lambda x: x[0])
    _ST = {"selected": best[:1].decode("ascii"), "candidates": {c[:1].decode("ascii"): len(c) - 1 for _, c in out}}
    return best

def decompress(data):
    tag = data[:1]
    body = data[1:]
    if tag == b"R":
        return _R["decompress"](body)
    if tag == b"G":
        return _G["decompress"](body)
    if tag == b"S":
        return _S["decompress"](body)
    raise ValueError("bad selector tag")

def stats():
    return dict(_ST)
