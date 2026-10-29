"""Original OrderedStream candidate. Independent qualification is pending."""

class OrderedStream:
    def __init__(self, n):
        self._values = [None] * n
        self._next = 0

    def insert(self, idKey, value):
        self._values[idKey - 1] = value
        chunk = []
        while self._next < len(self._values) and self._values[self._next] is not None:
            chunk.append(self._values[self._next])
            self._next += 1
        return chunk
