"""715. Range Module."""

class _Node:
    __slots__ = ('covered', 'left', 'right')

    def __init__(self, covered=False):
        self.covered = covered
        self.left = None
        self.right = None


class RangeModule:
    """Dynamic segment tree over half-open integer intervals; O(log U) per operation."""
    def __init__(self):
        self.root = _Node()

    def _assign(self, node, low, high, left, right, covered):
        if left <= low and high <= right:
            node.covered = covered
            node.left = node.right = None
            return
        if node.covered is not None:
            node.left = _Node(node.covered)
            node.right = _Node(node.covered)
            node.covered = None
        middle = (low + high) // 2
        if left < middle:
            self._assign(node.left, low, middle, left, right, covered)
        if right > middle:
            self._assign(node.right, middle, high, left, right, covered)
        if node.left.covered is not None and node.left.covered == node.right.covered:
            node.covered = node.left.covered
            node.left = node.right = None

    def _query(self, node, low, high, left, right):
        if node.covered is not None:
            return node.covered
        if left <= low and high <= right:
            return False
        middle = (low + high) // 2
        if right <= middle:
            return self._query(node.left, low, middle, left, right)
        if left >= middle:
            return self._query(node.right, middle, high, left, right)
        return (self._query(node.left, low, middle, left, right)
                and self._query(node.right, middle, high, left, right))

    def addRange(self, left: int, right: int) -> None:
        self._assign(self.root, 0, 1_000_000_000, left, right, True)

    def removeRange(self, left: int, right: int) -> None:
        self._assign(self.root, 0, 1_000_000_000, left, right, False)

    def queryRange(self, left: int, right: int) -> bool:
        return self._query(self.root, 0, 1_000_000_000, left, right)


def solve(operations: list[str], arguments: list[list]) -> list:
    """Replay the native LeetCode interface with one request-local instance."""
    if not operations:
        return []
    instance = RangeModule(*arguments[0])
    result = [None]
    for operation, values in zip(operations[1:], arguments[1:]):
        result.append(getattr(instance, operation)(*values))
    return result


Solution = RangeModule
