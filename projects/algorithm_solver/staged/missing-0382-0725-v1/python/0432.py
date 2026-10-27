"""432. All O`one Data Structure."""

class _Bucket:
    def __init__(self, count):
        self.count = count
        self.keys = set()
        self.previous = None
        self.next = None


class AllOne:
    """Ordered count buckets and key ownership; expected O(1) per operation."""
    def __init__(self):
        self.head = _Bucket(0)
        self.tail = _Bucket(0)
        self.head.next = self.tail
        self.tail.previous = self.head
        self.owner = {}

    def _after(self, previous, count):
        node = _Bucket(count)
        node.previous, node.next = previous, previous.next
        previous.next.previous = node
        previous.next = node
        return node

    def _discard_empty(self, node):
        if node is not self.head and node is not self.tail and not node.keys:
            node.previous.next = node.next
            node.next.previous = node.previous

    def inc(self, key: str) -> None:
        source = self.owner.get(key, self.head)
        target = source.next
        if target is self.tail or target.count != source.count + 1:
            target = self._after(source, source.count + 1)
        target.keys.add(key)
        self.owner[key] = target
        if source is not self.head:
            source.keys.remove(key)
            self._discard_empty(source)

    def dec(self, key: str) -> None:
        source = self.owner[key]
        if source.count == 1:
            del self.owner[key]
        else:
            target = source.previous
            if target is self.head or target.count != source.count - 1:
                target = self._after(source.previous, source.count - 1)
            target.keys.add(key)
            self.owner[key] = target
        source.keys.remove(key)
        self._discard_empty(source)

    def getMaxKey(self) -> str:
        return next(iter(self.tail.previous.keys), '')

    def getMinKey(self) -> str:
        return next(iter(self.head.next.keys), '')


def solve(operations: list[str], arguments: list[list]) -> list:
    """Replay the native LeetCode interface with one request-local instance."""
    if not operations:
        return []
    instance = AllOne(*arguments[0])
    result = [None]
    for operation, values in zip(operations[1:], arguments[1:]):
        result.append(getattr(instance, operation)(*values))
    return result


Solution = AllOne
