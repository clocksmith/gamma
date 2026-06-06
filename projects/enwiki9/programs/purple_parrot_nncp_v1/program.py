"""purple_parrot_nncp_v1: online char-LSTM + arithmetic coder.

Non-cmix neural compression. Pure numpy + Python stdlib. No torch.
No pretrained weights. Weights are PRNG-seeded at start of run, so
the archive carries zero parameter cost; compressed size is just the
arithmetic-coded entropy of next-byte under the online language model.

Per-byte loop (encoder):
    probs   <- forward(prev_byte, h, c)        # (256,) distribution
    target  <- data[i]
    encode(probs, target)                      # arith range coder
    sgd_update(probs, target)                  # backprop one step
    advance (h, c, prev_byte)

Per-byte loop (decoder):
    probs   <- forward(prev_byte, h, c)        # IDENTICAL compute to encoder
    target  <- decode(probs)                   # recover encoder's symbol
    sgd_update(probs, target)                  # IDENTICAL gradient
    advance (h, c, prev_byte)

The LSTM weights, hidden state, and numerical sequence are bit-identical
between encoder and decoder because they perform the same operations in
the same order on the same byte stream. This requires:
    * fixed PRNG seed for init
    * deterministic numpy ops (single-thread; same numpy build on host)
    * float32 throughout (no silent upcast to float64)

NOT BPTT yet. Gradients flow through one timestep only. Long-term memory
comes from the carried (h, c). v2 will add truncated BPTT (K=8) and
multi-layer / larger hidden.

Hyperparameters are LOCKED. Changing them invalidates all prior archives.
"""
import struct
import numpy as np

# --- locked hyperparameters ----------------------------------------------
SEED  = 0x5EED          # PRNG seed for weight init
H     = 128             # LSTM hidden size
E     = 32              # embedding dim
A     = 256             # byte alphabet
LR    = 0.05            # SGD learning rate
PREC  = 14              # arith coder precision: counts sum to 2**PREC
INIT  = 0.1             # weight init scale (std of standard_normal)
FBIAS = 1.0             # forget gate bias initial value
GCLIP = 5.0             # per-tensor L2 gradient clip threshold
BOS   = 0               # sentinel previous-byte at sequence start

# --- PRNG-seeded weight init ---------------------------------------------
def _init_weights():
    r = np.random.default_rng(SEED)
    W_e = (r.standard_normal((A, E)) * INIT).astype(np.float32)
    W_x = (r.standard_normal((4 * H, E)) * INIT).astype(np.float32)
    W_h = (r.standard_normal((4 * H, H)) * INIT).astype(np.float32)
    B   = np.zeros(4 * H, dtype=np.float32)
    B[H:2*H] = FBIAS
    W_o = (r.standard_normal((A, H)) * INIT).astype(np.float32)
    b_o = np.zeros(A, dtype=np.float32)
    return [W_e, W_x, W_h, B, W_o, b_o]

# --- numerical helpers (clipped for stability) ---------------------------
def _sig(x): return (1.0 / (1.0 + np.exp(-np.clip(x, -30.0, 30.0)))).astype(np.float32)
def _tnh(x): return np.tanh(np.clip(x, -30.0, 30.0)).astype(np.float32)

def _softmax(z):
    z = z - float(z.max())
    e = np.exp(z, dtype=np.float32)
    s = float(e.sum())
    return e / s

# --- LSTM step forward + backward ----------------------------------------
def _lstm_fwd(x, h, c, W_x, W_h, B):
    z = W_x @ x + W_h @ h + B
    i = _sig(z[:H])
    f = _sig(z[H:2*H])
    g = _tnh(z[2*H:3*H])
    o = _sig(z[3*H:4*H])
    c1 = f * c + i * g
    h1 = o * _tnh(c1)
    return h1.astype(np.float32), c1.astype(np.float32), (i, f, g, o, c, c1, x, h)

def _lstm_bwd(dh, dc, cache, W_x, W_h):
    i, f, g, o, c0, c1, x, h0 = cache
    tc1 = _tnh(c1)
    do = dh * tc1
    dctot = dh * o * (1.0 - tc1 * tc1) + dc
    df = dctot * c0
    dc0 = dctot * f
    di = dctot * g
    dg = dctot * i
    dz = np.concatenate([
        di * i * (1.0 - i),
        df * f * (1.0 - f),
        dg * (1.0 - g * g),
        do * o * (1.0 - o),
    ]).astype(np.float32)
    dW_x = np.outer(dz, x).astype(np.float32)
    dW_h = np.outer(dz, h0).astype(np.float32)
    dB   = dz
    dx   = (W_x.T @ dz).astype(np.float32)
    dh0  = (W_h.T @ dz).astype(np.float32)
    return dh0, dc0, dx, dW_x, dW_h, dB

# --- forward pass: prev_byte -> (probs, h1, c1, cache) -------------------
def _forward(prev_byte, h, c, params):
    W_e, W_x, W_h, B, W_o, b_o = params
    x = W_e[prev_byte]
    h1, c1, cache = _lstm_fwd(x, h, c, W_x, W_h, B)
    logits = W_o @ h1 + b_o
    probs = _softmax(logits)
    return probs, h1, c1, cache

# --- one SGD step on cross-entropy loss for `target` ---------------------
def _train(prev_byte, target, probs, h1, cache, params):
    W_e, W_x, W_h, B, W_o, b_o = params
    dlogits = probs.astype(np.float32).copy()
    dlogits[target] -= 1.0
    dW_o = np.outer(dlogits, h1).astype(np.float32)
    db_o = dlogits
    dh1  = (W_o.T @ dlogits).astype(np.float32)
    dc1  = np.zeros(H, dtype=np.float32)
    _, _, dx, dW_x, dW_h, dB = _lstm_bwd(dh1, dc1, cache, W_x, W_h)
    # per-tensor L2 clip
    for ga in (dW_o, dW_x, dW_h):
        n = float(np.linalg.norm(ga))
        if n > GCLIP:
            ga *= np.float32(GCLIP / n)
    # in-place SGD updates (mutates the arrays inside `params`)
    W_o   -= LR * dW_o
    b_o   -= LR * db_o
    W_x   -= LR * dW_x
    W_h   -= LR * dW_h
    B     -= LR * dB
    W_e[prev_byte] -= LR * dx

# --- probability vector -> integer cumulative counts ---------------------
# All counts >= 1; sum == 2**PREC; deterministic adjustment.
def _cum_counts(probs):
    T = 1 << PREC
    p64 = probs.astype(np.float64)
    c = np.floor(p64 * T).astype(np.int64)
    c[c < 1] = 1
    diff = T - int(c.sum())
    if diff > 0:
        order = np.argsort(-p64, kind='stable')
        for k in range(diff):
            c[int(order[k % A])] += 1
    elif diff < 0:
        deficit = -diff
        while deficit > 0:
            j = int(np.argmax(c))
            if c[j] <= 1:
                break
            take = min(int(c[j]) - 1, deficit)
            c[j] -= take
            deficit -= take
    cum = np.zeros(A + 1, dtype=np.int64)
    np.cumsum(c, out=cum[1:])
    return cum

# --- bit I/O -------------------------------------------------------------
class _BW:
    __slots__ = ('buf', 'cur', 'n')
    def __init__(self):
        self.buf = bytearray(); self.cur = 0; self.n = 0
    def w(self, b):
        self.cur = ((self.cur << 1) | (b & 1)) & 0xFF
        self.n += 1
        if self.n == 8:
            self.buf.append(self.cur); self.cur = 0; self.n = 0
    def flush(self):
        if self.n > 0:
            self.buf.append((self.cur << (8 - self.n)) & 0xFF)
        return bytes(self.buf)

class _BR:
    __slots__ = ('b', 'i', 'cur', 'n')
    def __init__(self, b):
        self.b = b; self.i = 0; self.cur = 0; self.n = 0
    def r(self):
        if self.n == 0:
            self.cur = self.b[self.i] if self.i < len(self.b) else 0
            self.i += 1
            self.n = 8
        bit = (self.cur >> 7) & 1
        self.cur = (self.cur << 1) & 0xFF
        self.n -= 1
        return bit

# --- 32-bit Witten-Neal-Cleary arithmetic coder --------------------------
TOP  = 1 << 32
HALF = 1 << 31
QTR  = 1 << 30

class _AE:
    __slots__ = ('lo', 'hi', 'pending', 'bw')
    def __init__(self):
        self.lo = 0; self.hi = TOP - 1; self.pending = 0; self.bw = _BW()
    def _emit(self, b):
        self.bw.w(b)
        for _ in range(self.pending):
            self.bw.w(1 - b)
        self.pending = 0
    def enc(self, cum, sym):
        total = int(cum[A])
        cl = int(cum[sym]); ch = int(cum[sym + 1])
        rng = self.hi - self.lo + 1
        self.hi = self.lo + (rng * ch) // total - 1
        self.lo = self.lo + (rng * cl) // total
        while True:
            if self.hi < HALF:
                self._emit(0)
            elif self.lo >= HALF:
                self._emit(1); self.lo -= HALF; self.hi -= HALF
            elif self.lo >= QTR and self.hi < HALF + QTR:
                self.pending += 1; self.lo -= QTR; self.hi -= QTR
            else:
                break
            self.lo <<= 1
            self.hi = (self.hi << 1) | 1
    def fin(self):
        self.pending += 1
        self._emit(0 if self.lo < QTR else 1)
        return self.bw.flush()

class _AD:
    __slots__ = ('lo', 'hi', 'code', 'br')
    def __init__(self, blob):
        self.lo = 0; self.hi = TOP - 1; self.br = _BR(blob); self.code = 0
        for _ in range(32):
            self.code = (self.code << 1) | self.br.r()
    def _query(self, total):
        rng = self.hi - self.lo + 1
        return ((self.code - self.lo + 1) * total - 1) // rng
    def find_sym(self, cum):
        total = int(cum[A])
        v = self._query(total)
        # binary search cum[] for the symbol whose interval contains v
        lo, hi = 0, A
        while lo < hi - 1:
            m = (lo + hi) >> 1
            if cum[m] <= v: lo = m
            else: hi = m
        return lo
    def upd(self, cum, sym):
        total = int(cum[A])
        cl = int(cum[sym]); ch = int(cum[sym + 1])
        rng = self.hi - self.lo + 1
        self.hi = self.lo + (rng * ch) // total - 1
        self.lo = self.lo + (rng * cl) // total
        while True:
            if self.hi < HALF:
                pass
            elif self.lo >= HALF:
                self.lo -= HALF; self.hi -= HALF; self.code -= HALF
            elif self.lo >= QTR and self.hi < HALF + QTR:
                self.lo -= QTR; self.hi -= QTR; self.code -= QTR
            else:
                break
            self.lo <<= 1
            self.hi = (self.hi << 1) | 1
            self.code = (self.code << 1) | self.br.r()

# --- public API ----------------------------------------------------------
def compress(data):
    n = len(data)
    if n == 0:
        return struct.pack(">Q", 0)
    params = _init_weights()
    h = np.zeros(H, dtype=np.float32)
    c = np.zeros(H, dtype=np.float32)
    ae = _AE()
    prev = BOS
    for i in range(n):
        probs, h1, c1, cache = _forward(prev, h, c, params)
        target = data[i]
        cum = _cum_counts(probs)
        ae.enc(cum, target)
        _train(prev, target, probs, h1, cache, params)
        h, c = h1, c1
        prev = target
    payload = ae.fin()
    return struct.pack(">Q", n) + payload

def decompress(arch):
    if len(arch) < 8:
        return b""
    n = struct.unpack(">Q", arch[:8])[0]
    if n == 0:
        return b""
    params = _init_weights()
    h = np.zeros(H, dtype=np.float32)
    c = np.zeros(H, dtype=np.float32)
    ad = _AD(arch[8:])
    out = bytearray(n)
    prev = BOS
    for i in range(n):
        probs, h1, c1, cache = _forward(prev, h, c, params)
        cum = _cum_counts(probs)
        sym = ad.find_sym(cum)
        ad.upd(cum, sym)
        out[i] = sym
        _train(prev, sym, probs, h1, cache, params)
        h, c = h1, c1
        prev = sym
    return bytes(out)

def stats():
    return {
        "arch": "char-LSTM(1) + softmax + 32-bit arith coder",
        "hidden": H, "embed": E, "alphabet": A,
        "lr": LR, "prec_bits": PREC, "init_seed": SEED,
        "bptt": 1, "layers": 1,
        "weights_archive_cost": 0,
        "weights_program_cost": "PRNG-seeded; only init code counted",
    }
