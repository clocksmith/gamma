"""Hack2Hire 67b36a7975074948935624c7 (MultiStream Reader); INFERRED spec, streams injected as strings; qualification unknown."""
CHUNK = 4


class Stream:
    """Read-only stream; only read(n) is used by the reader."""
    def __init__(self, data):
        self._data, self._pos = data, 0

    def read(self, n):
        piece = self._data[self._pos:self._pos + n]
        self._pos += len(piece)
        return piece


class MultiStreamReader:
    def __init__(self, streams):
        self.streams = [Stream(s) for s in streams]
        self.current = 0
        self.pending = ''

    def read(self, n):
        parts, need = [], n
        if self.pending:
            take = self.pending[:need]; parts.append(take); self.pending = self.pending[len(take):]; need -= len(take)
        while need > 0 and self.current < len(self.streams):
            chunk = self.streams[self.current].read(max(CHUNK, need))
            if chunk == '': self.current += 1; continue
            parts.append(chunk[:need]); self.pending = chunk[need:]; need -= min(need, len(chunk))
        return ''.join(parts)


def solve(operations, arguments):
    reader = MultiStreamReader(*arguments[0])
    return [None] + [getattr(reader, op)(*row) for op, row in zip(operations[1:], arguments[1:])]
