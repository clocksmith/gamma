"""2317. Maximum XOR After Operations: keep each available bit in exactly one final operand."""


def solve(nums: list[int]) -> int:
    """O(n) time and O(1) auxiliary space on the nonnegative 31-bit domain; inputs are read-only."""
    answer = 0
    for value in nums:
        answer |= value
    return answer


class Solution:
    def maximumXOR(self, nums: list[int]) -> int:
        return solve(nums)
