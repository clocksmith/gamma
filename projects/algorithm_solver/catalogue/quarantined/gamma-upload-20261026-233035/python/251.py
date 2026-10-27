"""251. Flatten 2D Vector."""
class Vector2D:
    def __init__(self, vec: list[list[int]]):
        self.vector = vec
        self.row = 0
        self.column = 0
        self._advance()

    def _advance(self):
        while self.row < len(self.vector) and self.column == len(self.vector[self.row]):
            self.row += 1
            self.column = 0

    def next(self) -> int:
        value = self.vector[self.row][self.column]
        self.column += 1
        self._advance()
        return value

    def hasNext(self) -> bool:
        return self.row < len(self.vector)

def solve(vec: list[list[int]], operations: list[str]) -> list:
    iterator = Vector2D(vec)
    return [getattr(iterator, operation)() for operation in operations]
