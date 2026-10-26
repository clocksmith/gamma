"""1860. Incremental Memory Leak: consume each successive allocation from the larger remaining stick with first-stick ties."""


def solve(memory1: int, memory2: int) -> list[int]:
    """O(sqrt(memory1 + memory2 + 1)) time and O(1) auxiliary space; inputs are read-only."""
    first, second = memory1, memory2
    time = 1
    while max(first, second) >= time:
        if first >= second:
            first -= time
        else:
            second -= time
        time += 1
    return [time, first, second]


class Solution:
    def memLeak(self, memory1: int, memory2: int) -> list[int]:
        return solve(memory1, memory2)
