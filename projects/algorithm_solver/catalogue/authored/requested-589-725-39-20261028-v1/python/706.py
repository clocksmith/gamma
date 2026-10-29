"""Original LeetCode 706 candidate; qualification unknown."""

from array import array

class MyHashMap:
    def __init__(self): self.values = array('i', [-1]) * 1000001
    def put(self, key, value): self.values[key] = value
    def get(self, key): return self.values[key]
    def remove(self, key): self.values[key] = -1


def solve(operations, arguments):
    instance = MyHashMap(*arguments[0])
    result = [None]
    for operation, values in zip(operations[1:], arguments[1:]):
        result.append(getattr(instance, operation)(*values))
    return result
