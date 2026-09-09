"""Integer pre-truth symbol calibration; synthetic reference, not native FX2.

Base counts must come from a decoder-rebuilt predictor. This component supplies
no pretrained model, frontend, or corpus compression claim.
"""
import hashlib
import json

Q = 65536
PRIOR = 32 * Q
ARMS = ('P', 'K', 'D', 'S')


def integers(values, size, upper, lower=0):
    return (isinstance(values, (list, tuple)) and len(values) == size
            and all(type(x) is int and lower <= x <= upper for x in values))


def normalized(counts):
    """Q16 mass conserved exactly; remainder ties follow symbol order."""
    total = sum(counts)
    rows = [divmod(x * Q, total) for x in counts]
    result = [x[0] for x in rows]
    order = sorted(range(len(rows)), key=lambda i: (-rows[i][1], i))
    for i in order[:Q - sum(result)]:
        result[i] += 1
    return result


class ResidualRatio:
    def __init__(self, size, arm='D'):
        if type(size) is not int or not 2 <= size <= 256 or arm not in ARMS:
            raise ValueError('invalid alphabet or arm')
        self.size, self.arm = size, arm
        self.observed = [0] * size
        self.expected = [0] * size
        self.position = 0
        self.pending = None

    def _correct(self, base):
        if self.arm in ('P', 'K'):
            return tuple(base)
        result = []
        for p, observed, expected in zip(base, self.observed, self.expected):
            numerator, denominator = PRIOR + observed, PRIOR + expected
            if numerator * 4 < denominator:
                numerator, denominator = 1, 4
            elif numerator > 4 * denominator:
                numerator, denominator = 4, 1
            result.append(max(1, p * numerator // denominator))
        return tuple(result)

    def predict(self, base):
        if self.pending is not None:
            raise ValueError('observe decoded symbol before predicting again')
        if self.position >= (1 << 63) - 1:
            raise ValueError('position limit')
        if not integers(base, self.size, 65535, 1):
            raise ValueError('base counts must be positive bounded integers')
        self.pending = tuple(base)
        return self._correct(self.pending)

    def observe(self, symbol):
        if self.pending is None:
            raise ValueError('predict must precede observe')
        if type(symbol) is not int or not 0 <= symbol < self.size:
            raise ValueError('invalid decoded symbol')
        if self.arm != 'P':
            expected = normalized(self.pending)
            for i in range(self.size):
                self.expected[i] += expected[i]
            target = (symbol + 1) % self.size if self.arm == 'S' else symbol
            self.observed[target] += Q
            if (self.position + 1) % 256 == 0:
                self.observed = [x // 2 for x in self.observed]
                self.expected = [x // 2 for x in self.expected]
        self.position += 1
        self.pending = None

    def serialize(self):
        value = dict(version=1, size=self.size, arm=self.arm,
                     observed=self.observed, expected=self.expected,
                     position=self.position, pending=self.pending)
        return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()

    def state_digest(self):
        return hashlib.sha256(self.serialize()).hexdigest()

    @classmethod
    def restore(cls, payload):
        if not isinstance(payload, bytes) or len(payload) > 16384:
            raise ValueError('checkpoint size/type limit')
        value = json.loads(payload)
        if not isinstance(value, dict) or set(value) != {
                'version', 'size', 'arm', 'observed', 'expected', 'position', 'pending'}:
            raise ValueError('checkpoint schema')
        if type(value['version']) is not int or value['version'] != 1:
            raise ValueError('checkpoint version')
        result = cls(value['size'], value['arm'])
        position = value['position']
        if type(position) is not int or not 0 <= position < (1 << 63):
            raise ValueError('checkpoint position')
        for name in ('observed', 'expected'):
            history = value[name]
            if not integers(history, result.size, 512 * Q):
                raise ValueError('checkpoint history')
            total = sum(history)
            if result.arm == 'P':
                valid = total == 0
            elif position < 256:
                valid = total == position * Q
            else:
                phase = position % 256
                valid = (phase + 128) * Q - 2 * result.size <= total <= (phase + 256) * Q
            if not valid:
                raise ValueError('history inconsistent with position')
            setattr(result, name, history)
        pending = value['pending']
        if pending is not None and not integers(pending, result.size, 65535, 1):
            raise ValueError('checkpoint pending counts')
        result.pending = tuple(pending) if pending is not None else None
        result.position = position
        # Reject duplicate keys, unknown whitespace variants, or altered types.
        if result.serialize() != payload:
            raise ValueError('checkpoint is not canonical')
        return result
