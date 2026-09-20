"""losslessly compressed variants of cpp_infer/data/weights.bin

the uncompressed format (pysrc/export_weights.py, cpp_infer/SPEC.md section 4)
stays the reference; this module writes/reads compressed containers that decode
to bit-for-bit identical tensors.  the C++ decoder lives in
cpp_infer/src/weights_io_compressed.cpp and must stay in exact sync.

format v1, magic FX2TFWC1: every DT_I8 tensor (the 15-value quantized weights,
ints in [-7, 7]) is range-coded with a uniform 1/15 model, i.e. log2(15) =
3.907 bits per weight; bf16/f32/i32 tensors and all metadata are stored raw.

format v2, magic FX2TFWC2: one range-coded stream with adaptive binary models
(LZMA-style 11-bit probabilities, shift-5 update):
  - rope.sin / rope.cos are not stored at all: the decoder recomputes them
    from rope.inv_freq with a bit-exact host port of CUDA libdevice
    __nv_sinf/__nv_cosf (the encoder verifies equality before dropping them,
    and falls back to storing the tables if they do not match)
  - DT_I8 quantized weights: adaptive 15-symbol bit tree (~order-0 entropy,
    3.79 bits/weight)
  - DT_BF16: adaptive byte models, low byte contexted on the high byte
  - DT_F32 / DT_I32: adaptive per-byte-plane models
  - names: order-2 adaptive character model; metadata: order-1 byte model

convert / verify from the command line (run from the repository root):
    python -m pysrc.weights_compress compress   cpp_infer/data/weights.bin cpp_infer/data/weights.c2
    python -m pysrc.weights_compress compress1  cpp_infer/data/weights.bin cpp_infer/data/weights.c1
    python -m pysrc.weights_compress decompress cpp_infer/data/weights.c2  /tmp/roundtrip.bin
    python -m pysrc.weights_compress verify     cpp_infer/data/weights.bin cpp_infer/data/weights.c2
(decompress/verify detect the format from the magic)
"""

import struct
import sys
from fractions import Fraction

import numpy as np

from pysrc.export_weights import (
    DTYPE_BF16_BITS,
    DTYPE_FLOAT32,
    DTYPE_INT8,
    DTYPE_INT32,
    _DTYPE_TO_NUMPY,
    read_tensor_file,
)

MAGIC_V1 = b"FX2TFWC1"

_TOP = 1 << 24
_MASK32 = 0xFFFFFFFF


class RangeEncoder:
    """LZMA-style byte-wise range coder (identical to the C++ decoder's model
    of the stream: 32-bit range, 64-bit low with carry propagation through a
    cache byte, renormalization at 2**24)"""

    def __init__(self) -> None:
        self.low = 0
        self.range = _MASK32
        self.cache = 0
        self.cache_size = 1
        self.out = bytearray()

    def _shift_low(self) -> None:
        if self.low < 0xFF000000 or self.low > _MASK32:
            carry = self.low >> 32
            self.out.append((self.cache + carry) & 0xFF)
            for _ in range(self.cache_size - 1):
                self.out.append((0xFF + carry) & 0xFF)
            self.cache = (self.low >> 24) & 0xFF
            self.cache_size = 0
        self.cache_size += 1
        self.low = (self.low << 8) & _MASK32

    def encode(self, cum: int, freq: int, tot: int) -> None:
        r = self.range // tot
        self.low += r * cum
        self.range = r * freq
        while self.range < _TOP:
            self.range = self.range << 8
            self._shift_low()

    def finish(self) -> bytes:
        for _ in range(5):
            self._shift_low()
        return bytes(self.out)


class RangeDecoder:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.pos = 1  # the first byte is the encoder's initial zero cache
        self.range = _MASK32
        self.code = 0
        for _ in range(4):
            self.code = (self.code << 8) | self._byte()

    def _byte(self) -> int:
        b = self.data[self.pos] if self.pos < len(self.data) else 0
        self.pos += 1
        return b

    def decode_uniform(self, tot: int) -> int:
        r = self.range // tot
        s = min(self.code // r, tot - 1)
        self.code -= r * s
        self.range = r
        while self.range < _TOP:
            self.code = ((self.code << 8) | self._byte()) & _MASK32
            self.range = self.range << 8
        return s


def _encode_i8_uniform15(values: np.ndarray) -> bytes:
    """range-code int8 values in [-7, 7] at log2(15) bits per value"""
    assert values.dtype == np.int8
    symbols = values.astype(np.int32).ravel() + 7
    assert symbols.min() >= 0 and symbols.max() <= 14
    enc = RangeEncoder()
    encode = enc.encode
    for s in symbols.tolist():
        encode(s, 1, 15)
    return enc.finish()


def _decode_i8_uniform15(stream: bytes, count: int) -> np.ndarray:
    dec = RangeDecoder(stream)
    decode = dec.decode_uniform
    out = np.empty(count, dtype=np.int8)
    out_list = [decode(15) - 7 for _ in range(count)]
    out[:] = out_list
    return out


def write_tensor_file_v1(
    filename: str, entries: list[tuple[str, int, np.ndarray]]
) -> None:
    """compressed alternative to export_weights.write_tensor_file: same
    entries, DT_I8 payloads range-coded at log2(15) bits/weight, rest raw"""
    with open(filename, "wb") as f:
        f.write(MAGIC_V1)
        f.write(struct.pack("<I", len(entries)))
        for name, dtype_code, array in entries:
            assert array.dtype == _DTYPE_TO_NUMPY[dtype_code], name
            data = np.ascontiguousarray(array)
            encoded = name.encode()
            f.write(struct.pack("<I", len(encoded)))
            f.write(encoded)
            f.write(struct.pack("<B", dtype_code))
            f.write(struct.pack("<I", data.ndim))
            f.write(struct.pack(f"<{data.ndim}I", *data.shape))
            if dtype_code == DTYPE_INT8:
                stream = _encode_i8_uniform15(data.reshape(-1))
                f.write(struct.pack("<I", len(stream)))
                f.write(stream)
            else:
                f.write(data.tobytes())


def read_tensor_file_v1(filename: str) -> dict[str, tuple[int, np.ndarray]]:
    with open(filename, "rb") as f:
        assert f.read(8) == MAGIC_V1
        (n_tensors,) = struct.unpack("<I", f.read(4))
        tensors: dict[str, tuple[int, np.ndarray]] = {}
        for _ in range(n_tensors):
            (name_length,) = struct.unpack("<I", f.read(4))
            name = f.read(name_length).decode()
            (dtype_code,) = struct.unpack("<B", f.read(1))
            (ndim,) = struct.unpack("<I", f.read(4))
            shape = struct.unpack(f"<{ndim}I", f.read(4 * ndim))
            dtype = np.dtype(_DTYPE_TO_NUMPY[dtype_code])
            count = int(np.prod(shape)) if ndim else 1
            if dtype_code == DTYPE_INT8:
                (stream_len,) = struct.unpack("<I", f.read(4))
                array = _decode_i8_uniform15(f.read(stream_len), count)
                array = array.reshape(shape)
            else:
                array = np.frombuffer(
                    f.read(count * dtype.itemsize), dtype=dtype
                ).reshape(shape)
            assert name not in tensors
            tensors[name] = (dtype_code, array)
        assert f.read(1) == b""
        return tensors


# ---------------------------------------------------------------------------
# format v2
# ---------------------------------------------------------------------------

MAGIC_V2 = b"FX2TFWC2"

# payload encodings (one byte per tensor in the v2 stream)
ENC_RAW = 0  # bytes through the order-0 raw model (fallback, any dtype)
ENC_INT4 = 1  # DT_I8 values in [-7, 7], adaptive 15-symbol tree
ENC_BF16 = 2  # DT_BF16, hi/lo byte models
ENC_PLANE4 = 3  # DT_F32/DT_I32, per-byte-plane models
ENC_ROPE_SIN = 4  # empty payload: recompute from rope.inv_freq
ENC_ROPE_COS = 5  # empty payload: recompute from rope.inv_freq


# --- bit-exact host emulation of CUDA libdevice __nv_sinf/__nv_cosf ---------
#
# algorithm transcribed from the __nv_sinf/__nv_cosf LLVM IR of
# /usr/local/cuda/nvvm/libdevice/libdevice.10.bc (CUDA 13.0): Cody-Waite
# 3-step FMA reduction for |a| < 105615, Payne-Hanek integer reduction above,
# shared polynomial kernel; cos is sin with quadrant + 1.
#
# float32 fmaf(x, y, z) is emulated as double(x)*double(y) + double(z) (the
# product is exact in double, so the double result is correctly rounded) then
# rounded to float32; that double rounding differs from a genuine single
# rounding only when the double lands within one double-ulp of a float32
# rounding boundary, which is detected and redone exactly with Fractions.

_F32_2_OVER_PI = np.uint32(0x3F22F983).view(np.float32)
_F32_RED = [np.uint32(u).view(np.float32) for u in (0xBFC90FDA, 0xB3A22168, 0xA7C234C5)]
_F32_KCOS = [np.uint32(u).view(np.float32) for u in (0x37CBAC00, 0xBAB607ED, 0x3D2AAABB, 0xBEFFFFFF)]
_F32_KSIN = [np.uint32(u).view(np.float32) for u in (0xB94D4153, 0x3C0885E4, 0xBE2AAAA8)]
_PH_SCALE = np.uint64(0x3BF921FB54442D19).view(np.float64)  # pi/2 * 2^-64
_I2OPI = (0x3C439041, 0xDB629599, 0xF534DDC0, 0xFC2757D1, 0x4E441529, 0xA2F9836E)
_TRIG_PLOSS = np.float32(105615.0)


def _round_fraction_to_f32(x: Fraction) -> np.float32:
    """round-to-nearest-even of an exact rational to float32 (finite range)"""
    if x == 0:
        return np.float32(0.0)
    f = np.float32(float(x))  # candidate; may be off by an ulp
    while True:
        below = np.nextafter(f, np.float32(-np.inf))
        above = np.nextafter(f, np.float32(np.inf))
        mid_below = (Fraction(float(f)) + Fraction(float(below))) / 2
        mid_above = (Fraction(float(f)) + Fraction(float(above))) / 2
        if x < mid_below:
            f = below
        elif x > mid_above:
            f = above
        elif x == mid_below:
            return below if int(below.view(np.uint32)) & 1 == 0 else f
        elif x == mid_above:
            return f if int(f.view(np.uint32)) & 1 == 0 else above
        else:
            return f


def _fmaf_vec(x: np.ndarray, y, z) -> np.ndarray:
    """float32 fused multiply-add, correctly rounded, on float32 arrays"""
    x64 = x.astype(np.float64)
    y64 = np.asarray(y, dtype=np.float32).astype(np.float64)
    z64 = np.asarray(z, dtype=np.float32).astype(np.float64)
    d = x64 * y64 + z64  # product exact in double -> one rounding, to double
    f = d.astype(np.float32)
    # double-rounding hazard: d within one double-ulp of a float32 boundary
    f64 = f.astype(np.float64)
    below = np.nextafter(f, np.float32(-np.inf)).astype(np.float64)
    above = np.nextafter(f, np.float32(np.inf)).astype(np.float64)
    ulp = np.spacing(np.abs(d))
    hazard = (np.abs(d - (f64 + below) * 0.5) <= ulp) | (
        np.abs(d - (f64 + above) * 0.5) <= ulp
    )
    for i in np.nonzero(hazard.ravel())[0]:
        xi = np.broadcast_to(x, f.shape).ravel()[i]
        yi = np.broadcast_to(np.asarray(y, dtype=np.float32), f.shape).ravel()[i]
        zi = np.broadcast_to(np.asarray(z, dtype=np.float32), f.shape).ravel()[i]
        exact = Fraction(float(xi)) * Fraction(float(yi)) + Fraction(float(zi))
        f.ravel()[i] = _round_fraction_to_f32(exact)
    return f


def _trig_slowpath(a: np.float32) -> tuple[np.float32, int]:
    """__internal_trig_reduction_slowpath: Payne-Hanek for |a| >= 105615"""
    ia = int(np.float32(a).view(np.uint32))
    sign = ia & 0x80000000
    e = ((ia >> 23) & 0xFF) - 128
    ia = ((ia << 8) | 0x80000000) & 0xFFFFFFFF
    result = []
    hi = 0
    for k in range(6):
        p = _I2OPI[k] * ia + hi
        result.append(p & 0xFFFFFFFF)
        hi = p >> 32
    result.append(hi)
    idx = 4 - (e >> 5)
    sh = e & 31
    rhi, rlo = result[idx + 2], result[idx + 1]
    if sh:
        rhi = ((result[idx + 2] << sh) | (result[idx + 1] >> (32 - sh))) & 0xFFFFFFFF
        rlo = ((result[idx + 1] << sh) | (result[idx] >> (32 - sh))) & 0xFFFFFFFF
    q = rhi >> 30
    nhi = ((rhi << 2) | (rlo >> 30)) & 0xFFFFFFFF
    nlo = (rlo << 2) & 0xFFFFFFFF
    top = nhi >> 31
    q += top
    if sign:
        q = -q
    s2 = sign
    if top:
        nhi ^= 0xFFFFFFFF
        nlo ^= 0xFFFFFFFF
        s2 = sign ^ 0x80000000
    prod = (nhi << 32) | nlo
    d = float(prod) * float(_PH_SCALE)  # sitofp to double, double multiply
    r = np.float32(d)  # fptrunc: rounds the genuine double, no hazard
    if s2:
        r = -r
    return r, q


def cuda_rope_table(inv_freq: np.ndarray, n_pos: int, cos: bool) -> np.ndarray:
    """(n_pos, len(inv_freq)) float32 table equal bit-for-bit to
    torch.outer(arange(n_pos), inv_freq).sin()/.cos() on a CUDA device"""
    assert inv_freq.dtype == np.float32 and inv_freq.ndim == 1
    t = np.arange(n_pos, dtype=np.float32)
    a = (t[:, None] * inv_freq[None, :]).astype(np.float32).ravel()

    # q = __float2int_rn(a * 2/pi); the product is exact in double, so one
    # float32 rounding; np.rint rounds half to even like cvt.rni
    m = (a.astype(np.float64) * float(_F32_2_OVER_PI)).astype(np.float32)
    q = np.rint(m).astype(np.int64)
    j = q.astype(np.float32)
    t_red = _fmaf_vec(j, _F32_RED[0], a)
    t_red = _fmaf_vec(j, _F32_RED[1], t_red)
    t_red = _fmaf_vec(j, _F32_RED[2], t_red)
    quadrant = q.copy()
    for i in np.nonzero(np.abs(a) >= _TRIG_PLOSS)[0]:
        t_red[i], quadrant[i] = _trig_slowpath(a[i])

    if cos:
        quadrant = quadrant + 1
    odd = (quadrant & 1) != 0
    x2 = (t_red.astype(np.float64) * t_red.astype(np.float64)).astype(np.float32)
    base = np.where(odd, np.float32(1.0), t_red)
    p = _fmaf_vec(x2, base, np.zeros_like(x2))
    c = np.where(odd, _fmaf_vec(np.full_like(x2, _F32_KCOS[0]), x2, np.full_like(x2, _F32_KCOS[1])), _F32_KSIN[0].astype(np.float32))
    c = _fmaf_vec(c, x2, np.where(odd, _F32_KCOS[2], _F32_KSIN[1]))
    c = _fmaf_vec(c, x2, np.where(odd, _F32_KCOS[3], _F32_KSIN[2]))
    z = _fmaf_vec(c, p, base)
    negate = (quadrant & 2) != 0
    z = np.where(negate, (z * np.float32(-1.0)) + np.float32(0.0), z)
    return z.reshape(n_pos, len(inv_freq))


# --- adaptive binary range coder (LZMA-style, 11-bit probs, shift-5) ---------


class BinEncoder:
    def __init__(self) -> None:
        self.low = 0
        self.range = _MASK32
        self.cache = 0
        self.cache_size = 1
        self.out = bytearray()

    def _shift_low(self) -> None:
        if self.low < 0xFF000000 or self.low > _MASK32:
            carry = self.low >> 32
            self.out.append((self.cache + carry) & 0xFF)
            for _ in range(self.cache_size - 1):
                self.out.append((0xFF + carry) & 0xFF)
            self.cache = (self.low >> 24) & 0xFF
            self.cache_size = 0
        self.cache_size += 1
        self.low = (self.low << 8) & _MASK32

    def encode_bit(self, probs: list, idx: int, bit: int) -> None:
        p = probs[idx]
        bound = (self.range >> 11) * p
        if bit == 0:
            self.range = bound
            probs[idx] = p + ((2048 - p) >> 5)
        else:
            self.low += bound
            self.range -= bound
            probs[idx] = p - (p >> 5)
        while self.range < _TOP:
            self.range = self.range << 8
            self._shift_low()

    def encode_tree(self, probs: list, nbits: int, symbol: int) -> None:
        node = 1
        for k in range(nbits - 1, -1, -1):
            bit = (symbol >> k) & 1
            self.encode_bit(probs, node, bit)
            node = (node << 1) | bit

    def finish(self) -> bytes:
        for _ in range(5):
            self._shift_low()
        return bytes(self.out)


class BinDecoder:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.pos = 1  # the first byte is the encoder's initial zero cache
        self.range = _MASK32
        self.code = 0
        for _ in range(4):
            self.code = (self.code << 8) | self._byte()

    def _byte(self) -> int:
        b = self.data[self.pos] if self.pos < len(self.data) else 0
        self.pos += 1
        return b

    def decode_bit(self, probs: list, idx: int) -> int:
        p = probs[idx]
        bound = (self.range >> 11) * p
        if self.code < bound:
            self.range = bound
            probs[idx] = p + ((2048 - p) >> 5)
            bit = 0
        else:
            self.code -= bound
            self.range -= bound
            probs[idx] = p - (p >> 5)
            bit = 1
        while self.range < _TOP:
            self.code = ((self.code << 8) | self._byte()) & _MASK32
            self.range = self.range << 8
        return bit

    def decode_tree(self, probs: list, nbits: int) -> int:
        node = 1
        for _ in range(nbits):
            node = (node << 1) | self.decode_bit(probs, node)
        return node - (1 << nbits)


class _Models:
    """the adaptive model set of the v2 stream (same on both sides)"""

    def __init__(self) -> None:
        make = lambda: [1024] * 256  # bit-tree probs, indices 1..255 used
        self.meta = {}  # order-1: prev meta byte -> byte tree
        self.meta_prev = 0
        self.name = {}  # order-2: (prev2, prev1) -> byte tree
        self.raw = make()
        self.int4 = [1024] * 16  # 4-bit tree, symbols 0..14
        self.bf16_hi = make()
        self.bf16_lo = {}  # hi byte -> byte tree
        self.plane = [make() for _ in range(4)]
        self._make = make

    def meta_tree(self) -> list:
        t = self.meta.get(self.meta_prev)
        if t is None:
            t = self.meta[self.meta_prev] = self._make()
        return t

    def name_tree(self, c2: int, c1: int) -> list:
        t = self.name.get((c2, c1))
        if t is None:
            t = self.name[(c2, c1)] = self._make()
        return t

    def bf16_lo_tree(self, hi: int) -> list:
        t = self.bf16_lo.get(hi)
        if t is None:
            t = self.bf16_lo[hi] = self._make()
        return t


def _pick_encoding(
    name: str,
    dtype_code: int,
    array: np.ndarray,
    seen: dict[str, np.ndarray],
) -> int:
    if dtype_code == DTYPE_INT8:
        flat = array.astype(np.int32).ravel()
        if len(flat) == 0 or (flat.min() >= -7 and flat.max() <= 7):
            return ENC_INT4
        return ENC_RAW
    if dtype_code == DTYPE_BF16_BITS:
        return ENC_BF16
    if dtype_code == DTYPE_FLOAT32:
        if (
            name in ("rope.sin", "rope.cos")
            and array.ndim == 2
            and "rope.inv_freq" in seen
            and seen["rope.inv_freq"].shape == (array.shape[1],)
        ):
            table = cuda_rope_table(
                seen["rope.inv_freq"], array.shape[0], cos=name == "rope.cos"
            )
            if np.array_equal(
                table.view(np.uint32), np.ascontiguousarray(array).view(np.uint32)
            ):
                return ENC_ROPE_SIN if name == "rope.sin" else ENC_ROPE_COS
        return ENC_PLANE4
    if dtype_code == DTYPE_INT32:
        return ENC_PLANE4
    return ENC_RAW


def write_tensor_file_v2(
    filename: str, entries: list[tuple[str, int, np.ndarray]]
) -> None:
    """compressed alternative to export_weights.write_tensor_file (format v2)"""
    enc = BinEncoder()
    models = _Models()

    def put_meta(b: int) -> None:
        enc.encode_tree(models.meta_tree(), 8, b)
        models.meta_prev = b

    seen: dict[str, np.ndarray] = {}
    for name, dtype_code, array in entries:
        assert array.dtype == _DTYPE_TO_NUMPY[dtype_code], name
        data = np.ascontiguousarray(array)
        encoded = name.encode()
        assert len(encoded) <= 255, name

        put_meta(len(encoded))
        c2 = c1 = 0
        for ch in encoded:
            enc.encode_tree(models.name_tree(c2, c1), 8, ch)
            c2, c1 = c1, ch
        put_meta(dtype_code)
        assert data.ndim <= 255
        put_meta(data.ndim)
        for d in data.shape:
            for k in range(4):
                put_meta((d >> (8 * k)) & 0xFF)

        encoding = _pick_encoding(name, dtype_code, data, seen)
        put_meta(encoding)

        if encoding == ENC_INT4:
            probs = models.int4
            for v in (data.astype(np.int32).ravel() + 7).tolist():
                enc.encode_tree(probs, 4, v)
        elif encoding == ENC_BF16:
            for v in data.reshape(-1).tolist():
                hi = v >> 8
                enc.encode_tree(models.bf16_hi, 8, hi)
                enc.encode_tree(models.bf16_lo_tree(hi), 8, v & 0xFF)
        elif encoding == ENC_PLANE4:
            raw = data.tobytes()
            planes = models.plane
            for i, b in enumerate(raw):
                enc.encode_tree(planes[i & 3], 8, b)
        elif encoding in (ENC_ROPE_SIN, ENC_ROPE_COS):
            pass  # recomputed by the decoder
        else:
            assert encoding == ENC_RAW
            probs = models.raw
            for b in data.tobytes():
                enc.encode_tree(probs, 8, b)

        if dtype_code == DTYPE_FLOAT32:
            seen[name] = data

    with open(filename, "wb") as f:
        f.write(MAGIC_V2)
        f.write(struct.pack("<I", len(entries)))
        f.write(enc.finish())


def read_tensor_file_v2(filename: str) -> dict[str, tuple[int, np.ndarray]]:
    with open(filename, "rb") as f:
        assert f.read(8) == MAGIC_V2
        (n_tensors,) = struct.unpack("<I", f.read(4))
        dec = BinDecoder(f.read())
    models = _Models()

    def get_meta() -> int:
        b = dec.decode_tree(models.meta_tree(), 8)
        models.meta_prev = b
        return b

    tensors: dict[str, tuple[int, np.ndarray]] = {}
    for _ in range(n_tensors):
        name_len = get_meta()
        chars = bytearray()
        c2 = c1 = 0
        for _ in range(name_len):
            ch = dec.decode_tree(models.name_tree(c2, c1), 8)
            chars.append(ch)
            c2, c1 = c1, ch
        name = chars.decode()
        dtype_code = get_meta()
        ndim = get_meta()
        shape = []
        for _ in range(ndim):
            d = 0
            for k in range(4):
                d |= get_meta() << (8 * k)
            shape.append(d)
        shape = tuple(shape)
        count = int(np.prod(shape)) if ndim else 1
        encoding = get_meta()

        dtype = np.dtype(_DTYPE_TO_NUMPY[dtype_code])
        if encoding == ENC_INT4:
            assert dtype_code == DTYPE_INT8
            probs = models.int4
            array = np.array(
                [dec.decode_tree(probs, 4) - 7 for _ in range(count)],
                dtype=np.int8,
            ).reshape(shape)
        elif encoding == ENC_BF16:
            assert dtype_code == DTYPE_BF16_BITS
            vals = np.empty(count, dtype=np.uint16)
            for i in range(count):
                hi = dec.decode_tree(models.bf16_hi, 8)
                lo = dec.decode_tree(models.bf16_lo_tree(hi), 8)
                vals[i] = (hi << 8) | lo
            array = vals.reshape(shape)
        elif encoding == ENC_PLANE4:
            planes = models.plane
            raw = bytes(
                dec.decode_tree(planes[i & 3], 8) for i in range(count * 4)
            )
            array = np.frombuffer(raw, dtype=dtype).reshape(shape)
        elif encoding in (ENC_ROPE_SIN, ENC_ROPE_COS):
            assert dtype_code == DTYPE_FLOAT32 and len(shape) == 2
            inv_code, inv = tensors["rope.inv_freq"]
            assert inv_code == DTYPE_FLOAT32 and inv.shape == (shape[1],)
            array = cuda_rope_table(
                inv, shape[0], cos=encoding == ENC_ROPE_COS
            )
        else:
            assert encoding == ENC_RAW
            probs = models.raw
            raw = bytes(
                dec.decode_tree(probs, 8) for i in range(count * dtype.itemsize)
            )
            array = np.frombuffer(raw, dtype=dtype).reshape(shape)

        assert name not in tensors
        tensors[name] = (dtype_code, array)
    return tensors


def _entries_from_reference(filename: str) -> list[tuple[str, int, np.ndarray]]:
    """reference-file tensors in file order (read_tensor_file keeps order:
    python dicts preserve insertion order)"""
    return [
        (name, dtype_code, array)
        for name, (dtype_code, array) in read_tensor_file(filename).items()
    ]


def _verify_equal(
    reference: dict[str, tuple[int, np.ndarray]],
    decoded: dict[str, tuple[int, np.ndarray]],
) -> None:
    assert set(reference) == set(decoded)
    for name, (dtype_code, array) in reference.items():
        decoded_code, decoded_array = decoded[name]
        assert decoded_code == dtype_code, name
        assert decoded_array.shape == array.shape, name
        assert decoded_array.dtype == array.dtype, name
        assert np.array_equal(decoded_array, array), name


def _read_compressed(filename: str) -> dict[str, tuple[int, np.ndarray]]:
    with open(filename, "rb") as f:
        magic = f.read(8)
    if magic == MAGIC_V1:
        return read_tensor_file_v1(filename)
    if magic == MAGIC_V2:
        return read_tensor_file_v2(filename)
    raise ValueError(f"{filename}: unknown magic {magic!r}")


def main() -> None:
    import os

    usage = (
        "usage: python -m pysrc.weights_compress"
        " {compress|compress1|decompress|verify} <input> <output|compressed>"
    )
    if len(sys.argv) != 4:
        sys.exit(usage)
    command, a, b = sys.argv[1:]
    if command not in ("compress", "compress1", "decompress", "verify"):
        sys.exit(usage)

    # Check the input files up front so a typo is reported as such instead of
    # as a traceback from somewhere deep in the reader ("b" is an output file
    # for every command except "verify").
    inputs = [a, b] if command == "verify" else [a]
    for path in inputs:
        if not os.path.isfile(path):
            sys.exit(
                f"error: input file {path!r} does not exist"
                if not os.path.exists(path)
                else f"error: input file {path!r} is not a regular file"
            )

    if command in ("compress", "compress1"):
        entries = _entries_from_reference(a)
        writer = write_tensor_file_v2 if command == "compress" else write_tensor_file_v1
        writer(b, entries)
        _verify_equal(dict(read_tensor_file(a)), _read_compressed(b))
        print(
            f"{a} ({os.path.getsize(a)} bytes) -> {b} "
            f"({os.path.getsize(b)} bytes), round-trip verified bit-exact"
        )
    elif command == "decompress":
        from pysrc.export_weights import write_tensor_file

        tensors = _read_compressed(a)
        write_tensor_file(
            b, [(name, code, arr) for name, (code, arr) in tensors.items()]
        )
        print(f"{a} -> {b} ({os.path.getsize(b)} bytes)")
    elif command == "verify":
        _verify_equal(read_tensor_file(a), _read_compressed(b))
        print(f"{b} decodes bit-exactly to {a}")
    else:
        sys.exit(usage)


if __name__ == "__main__":
    main()
