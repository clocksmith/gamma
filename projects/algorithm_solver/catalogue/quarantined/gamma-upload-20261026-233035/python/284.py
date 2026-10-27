"""284. Peeking Iterator."""
class PeekingIterator:
    def __init__(self, iterator):
        self.iterator = iterator
        self.cached = iterator.next() if iterator.hasNext() else None
        self.available = self.cached is not None

    def peek(self) -> int:
        return self.cached

    def next(self) -> int:
        value = self.cached
        if self.iterator.hasNext():
            self.cached = self.iterator.next()
        else:
            self.cached = None
            self.available = False
        return value

    def hasNext(self) -> bool:
        return self.available

def solve(iterator, operations: list[str]) -> list:
    peeking = PeekingIterator(iterator)
    return [getattr(peeking, operation)() for operation in operations]
