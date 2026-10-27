"""384. Shuffle an Array."""

from random import randrange


class Solution:
    """Fisher-Yates on fresh copies; reset never exposes the retained original array."""
    def __init__(self, nums: list[int]):
        self.original = nums[:]

    def reset(self) -> list[int]:
        return self.original[:]

    def shuffle(self) -> list[int]:
        result = self.original[:]
        for i in range(len(result) - 1, 0, -1):
            j = randrange(i + 1)
            result[i], result[j] = result[j], result[i]
        return result


def solve(operations: list[str], arguments: list[list]) -> list:
    """Replay native operations on one request-local instance."""
    if not operations:
        return []
    instance = Solution(*arguments[0])
    result = [None]
    for operation, values in zip(operations[1:], arguments[1:]):
        result.append(getattr(instance, operation)(*values))
    return result
