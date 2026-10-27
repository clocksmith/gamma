"""381. Insert Delete GetRandom O(1) - Duplicates allowed."""
import random
from collections import defaultdict

class RandomizedCollection:
    def __init__(self):
        self.values = []
        self.indices = defaultdict(set)

    def insert(self, val: int) -> bool:
        fresh = not self.indices[val]
        self.indices[val].add(len(self.values))
        self.values.append(val)
        return fresh

    def remove(self, val: int) -> bool:
        if not self.indices[val]:
            return False
        index = self.indices[val].pop()
        last_index = len(self.values) - 1
        last = self.values[last_index]
        if index != last_index:
            self.values[index] = last
            self.indices[last].remove(last_index)
            self.indices[last].add(index)
        self.values.pop()
        return True

    def getRandom(self) -> int:
        return random.choice(self.values)

def solve(operations: list[str], arguments: list[list[int]]) -> list:
    structure = RandomizedCollection()
    result = []
    for operation, values in zip(operations, arguments):
        if operation == 'RandomizedCollection':
            result.append(None)
        else:
            result.append(getattr(structure, operation)(*values))
    return result
