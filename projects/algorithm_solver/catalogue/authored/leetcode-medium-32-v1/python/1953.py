"""1953. Maximum Number of Weeks for Which You Can Work: separate the largest project with milestones from the others."""


def solve(milestones: list[int]) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    total = sum(milestones)
    largest = max(milestones)
    other = total - largest
    return min(total, 2 * other + 1)


class Solution:
    def numberOfWeeks(self, milestones: list[int]) -> int:
        return solve(milestones)
