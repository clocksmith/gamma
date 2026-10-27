"""380. Insert Delete GetRandom O(1)."""
import random

class RandomizedSet:
    def __init__(self):
        self.values = []
        self.indices = {}

    def insert(self, val: int) -> bool:
        if val in self.indices:
            return False
        self.indices[val] = len(self.values)
        self.values.append(val)
        return True

    def remove(self, val: int) -> bool:
        if val not in self.indices:
            return False
        index = self.indices.pop(val)
        last = self.values.pop()
        if index < len(self.values):
            self.values[index] = last
            self.indices[last] = index
        return True

    def getRandom(self) -> int:
        return random.choice(self.values)

def solve(operations: list[str], arguments: list[list[int]]) -> list:
    structure = RandomizedSet()
    result = []
    for operation, values in zip(operations, arguments):
        if operation == 'RandomizedSet':
            result.append(None)
        else:
            result.append(getattr(structure, operation)(*values))
    return result
