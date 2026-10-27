"""519. Random Flip Matrix."""

from random import randrange


class Solution:
    """Lazy Fisher-Yates remapping; O(1) expected work per flip and O(flips) storage."""
    def __init__(self, m: int, n: int):
        self.rows = m
        self.cols = n
        self.remaining = m * n
        self.mapping = {}

    def flip(self) -> list[int]:
        ticket = randrange(self.remaining)
        self.remaining -= 1
        cell = self.mapping.get(ticket, ticket)
        replacement = self.mapping.get(self.remaining, self.remaining)
        self.mapping[ticket] = replacement
        self.mapping.pop(self.remaining, None)
        return [cell // self.cols, cell % self.cols]

    def reset(self) -> None:
        self.remaining = self.rows * self.cols
        self.mapping.clear()


def solve(operations: list[str], arguments: list[list]) -> list:
    """Replay native operations on one request-local instance."""
    if not operations:
        return []
    instance = Solution(*arguments[0])
    result = [None]
    for operation, values in zip(operations[1:], arguments[1:]):
        result.append(getattr(instance, operation)(*values))
    return result
