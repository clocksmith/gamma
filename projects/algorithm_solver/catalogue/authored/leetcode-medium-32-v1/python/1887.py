"""1887. Reduction Operations to Make the Array Elements Equal: sum the number of smaller distinct levels."""


def solve(nums: list[int]) -> int:
    """O(n log n) time and O(n) auxiliary space; inputs are read-only."""
    values = sorted(nums)
    levels = answer = 0
    for index in range(1, len(values)):
        if values[index] != values[index - 1]:
            levels += 1
        answer += levels
    return answer


class Solution:
    def reductionOperations(self, nums: list[int]) -> int:
        return solve(nums)
