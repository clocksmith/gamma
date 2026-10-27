"""677. Map Sum Pairs."""

class _TrieNode:
    def __init__(self):
        self.children = {}
        self.total = 0


class MapSum:
    def __init__(self):
        self.values = {}
        self.root = _TrieNode()

    def insert(self, key: str, val: int) -> None:
        delta = val - self.values.get(key, 0)
        self.values[key] = val
        node = self.root
        node.total += delta
        for char in key:
            if char not in node.children:
                node.children[char] = _TrieNode()
            node = node.children[char]
            node.total += delta

    def sum(self, prefix: str) -> int:
        node = self.root
        for char in prefix:
            node = node.children.get(char)
            if node is None:
                return 0
        return node.total


def solve(operations: list[str], arguments: list[list]) -> list:
    """Replay native operations on one request-local instance."""
    if not operations:
        return []
    instance = MapSum(*arguments[0])
    result = [None]
    for operation, values in zip(operations[1:], arguments[1:]):
        result.append(getattr(instance, operation)(*values))
    return result


Solution = MapSum
