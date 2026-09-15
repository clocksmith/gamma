"""Causal first-half residual projection; fixed parent, exact integer state."""
from array import array
from fractions import Fraction
import hashlib
import struct

from lib.fx2_residual_projection_v1 import Q, unpack, ln2_bounds, rational

AMPLITUDES = (0, 1024, 2048, 4096, 8192, 16384)
SCALE = 32768
GRID = 1 << 64


class Controller:
    """predict precedes observe; no second-half truth affects this block's m."""
    def __init__(self, shifted=False):
        self.shifted = bool(shifted)
        self.clock = 0
        self.pending = None
        self.reset()

    def reset(self):
        self.packed = [0] * 32
        self.residuals = [[0] * 32 for _ in range(8)]
        self.memory = [[0] * 32 for _ in range(8)]
        self.norm = [0] * 8

    def predict(self, c, packed):
        if self.pending is not None or not 1 <= c < Q:
            raise ValueError('invalid prediction order or count')
        phi = unpack(packed)
        position = self.clock % 512
        row = position % 8
        if position < 256:
            a, m = 0, 0
        else:
            m = self.norm[row]
            a = sum(x * y for x, y in zip(self.memory[row], phi))
        assert abs(a) <= m
        self.pending = (c, packed)
        return a, m

    def observe(self, y):
        if self.pending is None or y not in (0, 1):
            raise ValueError('invalid observation order or truth')
        c, packed = self.pending
        self.pending = None
        position = self.clock % 512
        if position < 256:
            byte, row = divmod(position, 8)
            if row and self.packed[byte] != packed:
                raise ValueError('hidden features changed within byte')
            self.packed[byte] = packed
            self.residuals[row][byte] = Q * y - c
        self.clock += 1
        if self.clock % 512 == 256:
            features = [unpack(p) for p in self.packed]
            offset = 17 if self.shifted else 0
            for row in range(8):
                self.memory[row] = [sum(features[i][j] * self.residuals[row][(i + offset) % 32]
                                        for i in range(32)) for j in range(32)]
                self.norm[row] = sum(map(abs, self.memory[row]))
        elif self.clock % 512 == 0:
            self.reset()

    def state(self):
        """Every mutable controller value; called after observe, never pending."""
        if self.pending is not None:
            raise ValueError('state witness requires completed observation')
        return (struct.pack('<Q32Q', self.clock, *self.packed)
                + struct.pack('<256i', *(v for r in self.residuals for v in r))
                + struct.pack('<256q8q', *(v for r in self.memory for v in r), *self.norm))


def corrected(c, k, a, m):
    if not 1 <= c < Q or k not in AMPLITUDES or m < 0 or abs(a) > m:
        raise ValueError('invalid correction domain')
    if not m or not k:
        return c
    den = Q * SCALE * m
    return max(1, min(Q - 1, (c * den + c * (Q - c) * k * a + den // 2) // den))


def feature_rows(features, modeled, coder):
    if len(features) != 96 * len(modeled) or len(coder) != 224 * len(modeled):
        raise ValueError('population extent differs')
    previous = None
    for i, (f, base) in enumerate(zip(struct.iter_unpack('<QHBB', features), struct.iter_unpack('<7I', coder))):
        packed, c, flags, y = f
        if (flags & ~15 or flags & 7 != i % 8 or y != (modeled[i // 8] >> (7 - i % 8)) & 1
                or not 1 <= c < Q or (c, y) != (base[1], base[6])):
            raise ValueError('event identity differs')
        if not flags & 8 and packed:
            raise ValueError('missing feature is nonzero')
        if i % 8 and (packed, flags & 8) != previous:
            raise ValueError('within-byte feature differs')
        previous = packed, flags & 8
        yield packed, c, y


def headroom(features, modeled, coder):
    """Certified zero-point slopes and rounding allowance, no fitted constants."""
    models = [Controller(), Controller(True)]
    vectors = [(array('q'), array('q')) for _ in models]
    slopes = [0, 0]
    terms = [0, 0]
    hist = [[0] * Q for _ in models]
    states = [hashlib.sha256(), hashlib.sha256()]
    distinct = active = 0
    for i, (packed, c, y) in enumerate(feature_rows(features, modeled, coder)):
        values = []
        for j, model in enumerate(models):
            a, m = model.predict(c, packed)
            vectors[j][0].append(a)
            vectors[j][1].append(m)
            values.append((a, m))
            if a:
                # Sum floor bounds on a*(y-p)/m, with a common exact grid.
                slopes[j] += (a * (Q * y - c) * GRID) // (m * Q)
                terms[j] += 1
                hist[j][c if y else Q - c] += 1
            model.observe(y)
            if i % 8 == 7:
                states[j].update(model.state())
        (a, m), (b, n) = values
        distinct += a * (n or 1) != b * (m or 1)
        active += bool(a)
    lo, _ = ln2_bounds()
    reports = []
    for j in range(2):
        gl = Fraction(slopes[j], GRID)
        gu = Fraction(slopes[j] + terms[j], GRID)
        rounding = Fraction(sum((n * Q * GRID + c * (Q + c) - 1) // (c * (Q + c))
                                for c, n in enumerate(hist[j]) if n), GRID)
        ideal = max(Fraction(), gu) / 2
        upper = (ideal + rounding) / lo
        reports.append(dict(arm='D' if j == 0 else 'S', slope_lower=rational(gl),
                            slope_upper=rational(gu), slope_diagnostic=float(gl),
                            rounding_upper_nats=rational(rounding),
                            rounded_upper_bits=rational(upper), rounded_upper_bits_diagnostic=float(upper),
                            state_sha256=states[j].hexdigest(), nonzero_events=terms[j],
                            finite_replay_permitted=upper > 16))
    return dict(schema='gamma.enwiki9.causal-residual-headroom.v1', events=8 * len(modeled),
                block_modeled_bytes=64, learn_modeled_bytes=32, amplitudes=list(AMPLITUDES),
                scale=SCALE, header_bytes=2, arms=reports, aligned_nonzero_events=active,
                distinct_control_probabilities=distinct, finite_archive_bound=False), vectors
