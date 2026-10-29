"""Original LeetCode 705 candidate; qualification unknown."""

class MyHashSet:
    def __init__(self): self.present = bytearray(1000001)
    def add(self, key): self.present[key] = 1
    def remove(self, key): self.present[key] = 0
    def contains(self, key): return bool(self.present[key])


def solve(operations, arguments):
    instance = MyHashSet(*arguments[0])
    result = [None]
    for operation, values in zip(operations[1:], arguments[1:]):
        result.append(getattr(instance, operation)(*values))
    return result
