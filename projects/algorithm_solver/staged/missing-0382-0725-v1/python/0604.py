"""604. Design Compressed String Iterator."""

class StringIterator:
    """Parse each run on demand; do not expand the compressed string."""
    def __init__(self, compressedString: str):
        self.source = compressedString
        self.index = 0
        self.remaining = 0
        self.char = ' '

    def _load(self):
        while self.remaining == 0 and self.index < len(self.source):
            self.char = self.source[self.index]
            self.index += 1
            while self.index < len(self.source) and '0' <= self.source[self.index] <= '9':
                self.remaining = self.remaining * 10 + ord(self.source[self.index]) - 48
                self.index += 1

    def next(self) -> str:
        self._load()
        if self.remaining == 0:
            return ' '
        self.remaining -= 1
        return self.char

    def hasNext(self) -> bool:
        self._load()
        return self.remaining > 0


def solve(operations: list[str], arguments: list[list]) -> list:
    """Replay native operations on one request-local instance."""
    if not operations:
        return []
    instance = StringIterator(*arguments[0])
    result = [None]
    for operation, values in zip(operations[1:], arguments[1:]):
        result.append(getattr(instance, operation)(*values))
    return result


Solution = StringIterator
