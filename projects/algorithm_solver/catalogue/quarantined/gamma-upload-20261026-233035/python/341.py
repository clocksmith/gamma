"""341. Flatten Nested List Iterator."""
class NestedIterator:
    def __init__(self, nestedList):
        self.stack = list(reversed(nestedList))

    def _advance(self):
        while self.stack and not self.stack[-1].isInteger():
            self.stack.extend(reversed(self.stack.pop().getList()))

    def next(self) -> int:
        self._advance()
        return self.stack.pop().getInteger()

    def hasNext(self) -> bool:
        self._advance()
        return bool(self.stack)

def solve(nestedList) -> list[int]:
    iterator = NestedIterator(nestedList)
    result = []
    while iterator.hasNext():
        result.append(iterator.next())
    return result
