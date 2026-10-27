"""706. Design HashMap."""

class MyHashMap:
    """Separate chaining implemented with lists rather than a built-in hash map."""
    def __init__(self):
        self.buckets = [[] for _ in range(1009)]

    def put(self, key: int, value: int) -> None:
        bucket = self.buckets[key % len(self.buckets)]
        for entry in bucket:
            if entry[0] == key:
                entry[1] = value
                return
        bucket.append([key, value])

    def get(self, key: int) -> int:
        for stored, value in self.buckets[key % len(self.buckets)]:
            if stored == key:
                return value
        return -1

    def remove(self, key: int) -> None:
        bucket = self.buckets[key % len(self.buckets)]
        for index, entry in enumerate(bucket):
            if entry[0] == key:
                bucket[index] = bucket[-1]
                bucket.pop()
                return


def solve(operations: list[str], arguments: list[list]) -> list:
    """Replay native operations on one request-local instance."""
    if not operations:
        return []
    instance = MyHashMap(*arguments[0])
    result = [None]
    for operation, values in zip(operations[1:], arguments[1:]):
        result.append(getattr(instance, operation)(*values))
    return result


Solution = MyHashMap
