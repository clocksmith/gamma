"""705. Design HashSet."""

class MyHashSet:
    """Direct bit addressing for the stated integer key domain 0..1,000,000."""
    def __init__(self):
        self.bits = bytearray((1_000_001 + 7) // 8)

    def add(self, key: int) -> None:
        self.bits[key >> 3] |= 1 << (key & 7)

    def remove(self, key: int) -> None:
        self.bits[key >> 3] &= 255 ^ (1 << (key & 7))

    def contains(self, key: int) -> bool:
        return bool(self.bits[key >> 3] & (1 << (key & 7)))


def solve(operations: list[str], arguments: list[list]) -> list:
    """Replay native operations on one request-local instance."""
    if not operations:
        return []
    instance = MyHashSet(*arguments[0])
    result = [None]
    for operation, values in zip(operations[1:], arguments[1:]):
        result.append(getattr(instance, operation)(*values))
    return result


Solution = MyHashSet
