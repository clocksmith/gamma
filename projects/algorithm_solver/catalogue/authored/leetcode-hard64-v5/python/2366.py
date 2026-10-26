"""2366. Minimum Replacements to Sort the Array. Greedily split from right to left."""


def solve(nums: list[int]) -> int:
    """O(n) time and O(1) space. Inputs are preserved."""
    bound = nums[-1]
    answer = 0
    for index in range(len(nums) - 2, -1, -1):
        value = nums[index]
        parts = (value + bound - 1) // bound
        answer += parts - 1
        bound = value // parts
    return answer


class Solution:
    def minimumReplacement(self, nums: list[int]) -> int:
        return solve(nums)
