"""1665. Minimum Initial Energy to Finish Tasks: greedy descending minimum-minus-actual ordering; O(n log n) time and O(n) space."""


def solve(tasks: list[list[int]]) -> int:
    energy = required = 0
    for actual, minimum in sorted(tasks, key=lambda task: task[0] - task[1]):
        if energy < minimum:
            required += minimum - energy
            energy = minimum
        energy -= actual
    return required


class Solution:
    def minimumEffort(self, tasks: list[list[int]]) -> int:
        return solve(tasks)
