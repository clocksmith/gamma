"""398. Random Pick Index."""

from random import randrange


class Solution:
    """Index buckets give O(1) draws after O(n) construction."""
    def __init__(self, nums: list[int]):
        self.indices = {}
        for index, value in enumerate(nums):
            self.indices.setdefault(value, []).append(index)

    def pick(self, target: int) -> int:
        indices = self.indices[target]
        return indices[randrange(len(indices))]


def solve(operations: list[str], arguments: list[list]) -> list:
    """Replay native operations on one request-local instance."""
    if not operations:
        return []
    instance = Solution(*arguments[0])
    result = [None]
    for operation, values in zip(operations[1:], arguments[1:]):
        result.append(getattr(instance, operation)(*values))
    return result
