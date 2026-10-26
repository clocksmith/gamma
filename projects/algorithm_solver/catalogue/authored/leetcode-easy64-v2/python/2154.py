"""2154. Keep Multiplying Found Values by Two (Easy).

Specification: https://leetcode.com/problems/keep-multiplying-found-values-by-two/description/
"""


def solve(nums: list[int], original: int) -> int:
    """O(n + log(M + 1)) expected time, O(n) space; M=max(nums), positive inputs."""
    values = set(nums)
    result = original
    while result in values:
        result *= 2
    return result


class Solution:
    def findFinalValue(self, nums: list[int], original: int) -> int:
        return solve(nums, original)
