"""460. LFU Cache."""

from collections import OrderedDict


class LFUCache:
    """Frequency buckets with LRU order; expected O(1) get/put and O(capacity) space."""
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.values = {}
        self.frequencies = {}
        self.buckets = {}
        self.minimum = 0

    def _touch(self, key):
        frequency = self.frequencies[key]
        del self.buckets[frequency][key]
        if not self.buckets[frequency]:
            del self.buckets[frequency]
            if self.minimum == frequency:
                self.minimum += 1
        self.frequencies[key] = frequency + 1
        self.buckets.setdefault(frequency + 1, OrderedDict())[key] = None

    def get(self, key: int) -> int:
        if key not in self.values:
            return -1
        self._touch(key)
        return self.values[key]

    def put(self, key: int, value: int) -> None:
        if self.capacity == 0:
            return
        if key in self.values:
            self.values[key] = value
            self._touch(key)
            return
        if len(self.values) == self.capacity:
            removed, _ = self.buckets[self.minimum].popitem(last=False)
            if not self.buckets[self.minimum]:
                del self.buckets[self.minimum]
            del self.values[removed]
            del self.frequencies[removed]
        self.values[key] = value
        self.frequencies[key] = 1
        self.buckets.setdefault(1, OrderedDict())[key] = None
        self.minimum = 1


def solve(operations: list[str], arguments: list[list]) -> list:
    """Replay the native LeetCode interface with one request-local instance."""
    if not operations:
        return []
    instance = LFUCache(*arguments[0])
    result = [None]
    for operation, values in zip(operations[1:], arguments[1:]):
        result.append(getattr(instance, operation)(*values))
    return result


Solution = LFUCache
