"""170. Two Sum III - Data structure design."""
from collections import Counter

class TwoSum:
    def __init__(self):
        self.counts = Counter()

    def add(self, number: int) -> None:
        self.counts[number] += 1

    def find(self, value: int) -> bool:
        for number, count in self.counts.items():
            other = value - number
            if other in self.counts and (other != number or count > 1):
                return True
        return False

def solve(operations: list[str], arguments: list[list[int]]) -> list:
    structure = TwoSum()
    result = []
    for operation, values in zip(operations, arguments):
        if operation == 'TwoSum':
            result.append(None)
        else:
            result.append(getattr(structure, operation)(*values))
    return result
