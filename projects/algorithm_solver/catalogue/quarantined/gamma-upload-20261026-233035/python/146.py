"""146. LRU Cache."""
class Node:
    def __init__(self, key=0, value=0):
        self.key = key
        self.value = value
        self.previous = None
        self.next = None

class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.nodes = {}
        self.head = Node()
        self.tail = Node()
        self.head.next = self.tail
        self.tail.previous = self.head

    def _remove(self, node):
        node.previous.next = node.next
        node.next.previous = node.previous

    def _append(self, node):
        node.previous = self.tail.previous
        node.next = self.tail
        self.tail.previous.next = node
        self.tail.previous = node

    def get(self, key: int) -> int:
        node = self.nodes.get(key)
        if node is None:
            return -1
        self._remove(node)
        self._append(node)
        return node.value

    def put(self, key: int, value: int) -> None:
        if key in self.nodes:
            node = self.nodes[key]
            node.value = value
            self._remove(node)
            self._append(node)
            return
        node = Node(key, value)
        self.nodes[key] = node
        self._append(node)
        if len(self.nodes) > self.capacity:
            oldest = self.head.next
            self._remove(oldest)
            del self.nodes[oldest.key]

def solve(operations: list[str], arguments: list[list[int]]) -> list:
    result = []
    cache = None
    for operation, values in zip(operations, arguments):
        if operation == 'LRUCache':
            cache = LRUCache(*values)
            result.append(None)
        else:
            result.append(getattr(cache, operation)(*values))
    return result
