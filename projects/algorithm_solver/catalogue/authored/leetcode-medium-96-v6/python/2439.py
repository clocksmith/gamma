"""2439. Minimize Maximum of Array: take the strongest ceiling-average lower bound among all prefixes."""


def solve(nums: list[int]) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    total = answer = 0
    for index, value in enumerate(nums):
        total += value
        answer = max(answer, (total + index) // (index + 1))
    return answer


class Solution:
    def minimizeArrayValue(self, nums: list[int]) -> int:
        return solve(nums)
