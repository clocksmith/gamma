"""Lossless prefix source macros. The decoder needs only the table and packet."""
from functools import lru_cache
import math

MAX_BYTES = 65536
MAX_DEPTH = 128


def validate(table, width):
    if width not in (6, 7, 8) or len(table) > (1 << width) - 2:
        raise ValueError('Invalid width/table capacity')
    if len(set(table)) != len(table):
        raise ValueError('Duplicate entry')
    for parts in table:
        if not isinstance(parts, tuple) or not 1 <= len(parts) <= 5:
            raise ValueError('Invalid constructor arity')
        if any(not isinstance(x, bytes) for x in parts) or not 1 <= sum(map(len, parts)) <= 160 or not b''.join(parts).strip():
            raise ValueError('Invalid literal/shell')
        for x in parts:
            x.decode('utf8')


def spelling(raw, width):
    return '0' * width + ''.join('1' + format(b, '08b') for b in raw) + '0'


class Encoder:
    def __init__(self, raw, table, width, occurrences=()):
        validate(table, width)
        if len(raw) > MAX_BYTES:
            raise ValueError('Source limit')
        raw.decode('utf8')
        self.raw, self.table, self.width = raw, table, width
        self.count_bits = math.ceil(16 / width) * width
        self.trie = {}
        for code, parts in enumerate(table, 2):
            if len(parts) == 1:
                node = self.trie
                for b in parts[0]: node = node.setdefault(b, {})
                node[None] = code
        codes = {parts: i for i, parts in enumerate(table, 2) if len(parts) > 1}
        self.macros = {}
        for start, end, parts, holes in occurrences:
            if parts not in codes: continue
            if not (0 <= start < end <= len(raw)) or any(not start <= a < b <= end or (a, b) == (start, end) for a, b in holes):
                raise ValueError('Nonproper macro operand')
            assembled = parts[0]
            for (a, b), suffix in zip(holes, parts[1:]): assembled += raw[a:b] + suffix
            if assembled != raw[start:end] or len(holes) != len(parts)-1:
                raise ValueError('Macro expansion differs from source')
            self.macros.setdefault(start, []).append((end, codes[parts], holes))
        self.matches = {}
        for start in range(len(raw)):
            node, pos, matches = self.trie, start, []
            while pos < len(raw) and raw[pos] in node:
                node = node[raw[pos]]; pos += 1
                if None in node: matches.append((pos, node[None]))
            self.matches[start] = matches

    @lru_cache(None)
    def options(self, start, end):
        values = [(stop, self.width, ('entry', code)) for stop, code in self.matches[start] if stop <= end]
        for stop, code, holes in self.macros.get(start, ()):
            if stop <= end:
                operands = [self.single(a, b) for a, b in holes]
                values.append((stop, self.width + sum(x[0] for x in operands), ('macro', code, tuple(x[1] for x in operands))))
        return values

    @lru_cache(None)
    def stream(self, start, end):
        # Backward two-state exact DP: normal and already-open spelling mode.
        costs = {end: 0}; opened = {end: 1}; choices = {}; spell_choices = {}
        for pos in range(end-1, start-1, -1):
            best = 9 + opened[pos+1]; spell_choices[pos] = ('byte',)
            # Closing spelling then taking an entry cannot reopen at this byte.
            for stop, cost, token in self.options(pos, end):
                value = 1 + cost + costs[stop]
                if value < best: best = value; spell_choices[pos] = ('entry', stop, token)
            opened[pos] = best
            costs[pos] = self.width + 9 + opened[pos+1]
            choices[pos] = ('spell',)
            for stop, cost, token in self.options(pos, end):
                value = cost + costs[stop]
                if value < costs[pos]: costs[pos] = value; choices[pos] = ('entry', stop, token)
        result = []; pos = start
        while pos < end:
            choice = choices[pos]
            if choice[0] == 'entry':
                _, pos, token = choice; result.append(token); continue
            first = pos; pos += 1
            while pos < end and spell_choices[pos][0] == 'byte': pos += 1
            result.append(('raw', self.raw[first:pos]))
            if pos < end:
                _, pos, token = spell_choices[pos]; result.append(token)
        return costs[start], tuple(result)

    @lru_cache(None)
    def single(self, start, end):
        cost, seq = self.stream(start, end)
        if len(seq) == 1: return cost, seq[0]
        best = (cost + self.width + self.count_bits, ('concat', seq))
        raw = (self.width + 9 * (end-start) + 1, ('raw', self.raw[start:end]))
        if raw[0] < best[0]: best = raw
        for stop, cost, token in self.options(start, end):
            if stop == end and cost < best[0]: best = (cost, token)
        return best

    def encode(self):
        if not self.raw: return '', []
        _, seq = self.stream(0, len(self.raw))
        def emit(token):
            kind = token[0]
            if kind == 'raw': return spelling(token[1], self.width)
            if kind == 'entry': return format(token[1], f'0{self.width}b')
            if kind == 'macro': return format(token[1], f'0{self.width}b') + ''.join(emit(x) for x in token[2])
            if len(token[1]) >= 65536: raise ValueError('Concat count limit')
            return format(1, f'0{self.width}b') + format(len(token[1]), f'0{self.count_bits}b') + ''.join(emit(x) for x in token[1])
        bits = ''.join(emit(x) for x in seq)
        assert len(bits) == self.stream(0, len(self.raw))[0]
        self.options.cache_clear(); self.stream.cache_clear(); self.single.cache_clear()
        return bits, seq


def decode(bits, table, width):
    validate(table, width)
    if not isinstance(bits, str) or len(bits) > MAX_BYTES * 32 or set(bits) - {'0', '1'}:
        raise ValueError('Invalid bitstream')
    pos = 0; stats = {'primary_selections': 0, 'spelled_bytes': 0, 'spelling_payload_bits': 0,
                      'transition_bits': 0, 'concat_count_bits': 0, 'count_words': 0, 'macro_calls': 0, 'entry_uses': {}}
    def read(n):
        nonlocal pos
        if pos+n > len(bits): raise ValueError('Truncated operand')
        value = int(bits[pos:pos+n], 2); pos += n; return value
    def one(depth=0, context="operand"):
        if context in ("root", "concat") and bits[pos:pos+width] == format(1, f"0{width}b"):
            raise ValueError("Root or directly nested CONCAT")
        if depth > MAX_DEPTH: raise ValueError('Nesting limit')
        code = read(width); stats['primary_selections'] += 1
        if code == 0:
            raw = bytearray()
            while read(1):
                raw.append(read(8)); stats['spelled_bytes'] += 1
                if len(raw) > MAX_BYTES: raise ValueError('Expansion limit')
            if not raw: raise ValueError('Empty spelling run')
            stats['transition_bits'] += 1
            stats['spelling_payload_bits'] += 9 * len(raw)
            return bytes(raw)
        if code == 1:
            count_bits = math.ceil(16/width)*width; count = read(count_bits)
            stats['concat_count_bits'] += count_bits; stats['count_words'] += count_bits // width
            if not 2 <= count < 65536: raise ValueError('Noncanonical CONCAT')
            result = bytearray()
            previous_raw = False
            for _ in range(count):
                is_raw = bits[pos:pos+width] == "0" * width
                if previous_raw and is_raw: raise ValueError("Adjacent spelling runs")
                previous_raw = is_raw
                result.extend(one(depth+1, "concat"))
                if len(result) > MAX_BYTES: raise ValueError('Expansion limit')
            return bytes(result)
        if code-2 >= len(table): raise ValueError('Unused opcode')
        stats['entry_uses'][str(code-2)] = stats['entry_uses'].get(str(code-2), 0)+1
        parts = table[code-2]
        if len(parts)>1: stats['macro_calls'] += 1
        result = bytearray(parts[0])
        for suffix in parts[1:]:
            result.extend(one(depth+1)); result.extend(suffix)
            if len(result)>MAX_BYTES: raise ValueError('Expansion limit')
        return bytes(result)
    out = bytearray()
    previous_raw = False
    while pos < len(bits):
        is_raw = bits[pos:pos+width] == "0" * width
        if previous_raw and is_raw: raise ValueError("Adjacent spelling runs")
        previous_raw = is_raw
        out.extend(one(context="root"))
        if len(out)>MAX_BYTES: raise ValueError('Expansion limit')
    out.decode('utf8')
    assert len(bits) == stats['primary_selections']*width + stats['spelling_payload_bits'] + stats['transition_bits'] + stats['concat_count_bits']
    return bytes(out), stats


def packet(bits, width):
    padding = -len(bits) % 8
    return b'MFP1' + bytes([width]) + len(bits).to_bytes(4, 'big') + (int(bits+'0'*padding, 2).to_bytes((len(bits)+7)//8, 'big') if bits else b'')


def unpack(data, table, width):
    if len(data)<9 or data[:5] != b'MFP1'+bytes([width]): raise ValueError('Packet profile')
    n=int.from_bytes(data[5:9], 'big')
    if n>MAX_BYTES*32 or len(data)!=9+(n+7)//8: raise ValueError('Packet length')
    bits=''.join(format(b,'08b') for b in data[9:])
    if '1' in bits[n:]: raise ValueError('Nonzero padding')
    return decode(bits[:n],table,width)
