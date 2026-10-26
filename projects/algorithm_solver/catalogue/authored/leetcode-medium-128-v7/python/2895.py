"""2895. Minimum Processing Time: assign descending groups of four tasks to processors in increasing startup order."""


def solve(processorTime: list[int], tasks: list[int]) -> int:
    """O(n log n) time and O(n) auxiliary space; inputs are read-only."""
    processors = sorted(processorTime)
    ordered = sorted(tasks, reverse=True)
    return max(start + ordered[4 * index] for index, start in enumerate(processors))


class Solution:
    def minProcessingTime(self, processorTime: list[int], tasks: list[int]) -> int:
        return solve(processorTime, tasks)
