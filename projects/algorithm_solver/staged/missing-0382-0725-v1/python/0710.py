"""710. Random Pick with Blacklist."""

from random import randrange


class BlacklistPicker:
    """Remap forbidden low indices into allowed high indices; O(b) setup, O(1) pick."""
    def __init__(self, n: int, blacklist: list[int]):
        blocked = set(blacklist)
        self.limit = n - len(blacklist)
        self.mapping = {}
        replacement = self.limit
        for value in blacklist:
            if value >= self.limit:
                continue
            while replacement in blocked:
                replacement += 1
            self.mapping[value] = replacement
            replacement += 1

    def pick(self) -> int:
        value = randrange(self.limit)
        return self.mapping.get(value, value)


def solve(operations: list[str], arguments: list[list]) -> list:
    """Replay the native LeetCode interface with one request-local instance."""
    if not operations:
        return []
    instance = BlacklistPicker(*arguments[0])
    result = [None]
    for operation, values in zip(operations[1:], arguments[1:]):
        result.append(getattr(instance, operation)(*values))
    return result


Solution = BlacklistPicker
