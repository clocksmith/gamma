"""631. Design Excel Sum Formula."""

from collections import Counter


class Excel:
    """Store formulas as counted dependencies; evaluate a request-local DAG memo on demand."""
    def __init__(self, height: int, width: str):
        self.height = height
        self.width = ord(width) - ord('A') + 1
        self.values = {}
        self.formulas = {}

    def _key(self, row, column):
        return (row - 1) * self.width + ord(column) - ord('A')

    def _cell(self, address):
        return int(address[1:]), address[0]

    def set(self, row: int, column: str, val: int) -> None:
        key = self._key(row, column)
        self.formulas.pop(key, None)
        self.values[key] = val

    def get(self, row: int, column: str) -> int:
        memo = {}
        def evaluate(key):
            if key in memo:
                return memo[key]
            if key not in self.formulas:
                result = self.values.get(key, 0)
            else:
                result = sum(multiplicity * evaluate(dependency)
                             for dependency, multiplicity in self.formulas[key].items())
            memo[key] = result
            return result
        return evaluate(self._key(row, column))

    def sum(self, row: int, column: str, numbers: list[str]) -> int:
        dependencies = Counter()
        for expression in numbers:
            if ':' not in expression:
                r, c = self._cell(expression)
                dependencies[self._key(r, c)] += 1
            else:
                first, last = expression.split(':')
                r1, c1 = self._cell(first)
                r2, c2 = self._cell(last)
                for r in range(r1, r2 + 1):
                    for c in range(ord(c1), ord(c2) + 1):
                        dependencies[self._key(r, chr(c))] += 1
        key = self._key(row, column)
        self.formulas[key] = dependencies
        self.values.pop(key, None)
        return self.get(row, column)


def solve(operations: list[str], arguments: list[list]) -> list:
    """Replay native operations on one request-local instance."""
    if not operations:
        return []
    instance = Excel(*arguments[0])
    result = [None]
    for operation, values in zip(operations[1:], arguments[1:]):
        result.append(getattr(instance, operation)(*values))
    return result


Solution = Excel
