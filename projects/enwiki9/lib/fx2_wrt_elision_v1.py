"""Causal, conservative next-byte constraints for the pinned WRT encoder."""
import struct

ALL = (1 << 256) - 1


def swap(c):
    if 123 <= c < 127:
        c -= 43
    elif 80 <= c < 84:
        c += 43
    elif 58 <= c <= 63 or 74 <= c <= 79:
        c ^= 112
    if c in (88, 96):
        c ^= 56
    return c


def code(index):
    if not 0 <= index < 44880:
        raise ValueError('dictionary index outside source format')
    if index < 80:
        return bytes([128 + index])
    if index < 3920:
        q, r = divmod(index - 80, 80)
        return bytes([208 + q, 128 + r])
    q, r = divmod(index - 3920, 80)
    return bytes([240 + q // 32, 208 + q % 32, 128 + r])


def mask(values):
    value = 0
    for c in values:
        value |= 1 << c
    return value


def interval(prefix):
    depth = prefix.bit_length() - 1
    start = (prefix - (1 << depth)) << (8 - depth)
    return ((1 << (1 << (8 - depth))) - 1) << start


INTERVALS = tuple([ALL] + [interval(p) for p in range(1, 512)])


class Grammar:
    def __init__(self, word_count, vocabulary):
        if not 1 <= word_count <= 44880 or not vocabulary or any(not 0 <= c < 256 for c in vocabulary):
            raise ValueError('invalid immutable format inputs')
        self.vocab = mask(vocabulary)
        children = {}
        self.leaves = set()
        for i in range(word_count):
            word = code(i)
            self.leaves.add(word)
            for n, c in enumerate(word):
                children.setdefault(word[:n], set()).add(c)
        self.children = {k: mask(map(swap, v)) & self.vocab for k, v in children.items()}
        self.normal = (mask(map(swap, range(128))) | self.children[b'']) & self.vocab
        self.word = (mask(map(swap, range(97, 123))) | self.children[b'']) & self.vocab
        self.escaped = mask(map(swap, [6, 7, 12, 64, *range(128, 256)])) & self.vocab
        self.seen = 0
        self.prefix = 1
        self.pending = b''
        self.escape = False
        self.need_word = False

    def allowed(self):
        if not self.seen:
            return (1 << 7) & self.vocab
        if self.escape:
            return self.escaped
        if self.pending:
            return self.children[self.pending]
        return self.word if self.need_word else self.normal

    def forced(self, grammar=True):
        current = (self.allowed() if grammar else self.vocab)
        zero = bool(current & INTERVALS[2 * self.prefix])
        one = bool(current & INTERVALS[2 * self.prefix + 1])
        if not zero and not one:
            raise ValueError('decoded prefix outside admitted language')
        return None if zero and one else int(one)

    def observe(self, y):
        if y not in (0, 1):
            raise ValueError('not a bit')
        self.prefix = 2 * self.prefix + y
        if self.prefix < 256:
            return
        c = self.prefix - 256
        if not (self.allowed() >> c) & 1:
            raise ValueError('byte outside pre-truth language constraint')
        self.prefix = 1
        if not self.seen:
            self.seen = 1
            return
        self.seen += 1
        c = swap(c)
        if self.escape:
            self.escape = False
        elif self.pending:
            self.pending += bytes([c])
            if self.pending in self.leaves:
                self.pending = b''
                self.need_word = False
        elif c == 12:
            self.escape = True
        elif c in (6, 7, 64):
            self.need_word = True
        elif c >= 128:
            self.pending = bytes([c])
            if self.pending in self.leaves:
                self.pending = b''
            self.need_word = False
        else:
            self.need_word = False

    def state(self):
        # Immutable masks are determined by the separately bound vocabulary and
        # dictionary count. No omitted mutable predictor state exists.
        return struct.pack('<QHBBB3s', self.seen, self.prefix, self.escape,
                           self.need_word, len(self.pending), self.pending)

    def finish(self):
        if not self.seen or self.prefix != 1 or self.pending or self.escape or self.need_word:
            raise ValueError('incomplete WRT event at end of population')
