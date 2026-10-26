"""3251. Find the Count of Monotonic Pairs II.

Prefix sums aggregate valid preceding first-array values; O(n*M) time and O(M) space for M=max(nums). Inputs are preserved.
"""

def solve(nums: list[int]) -> int:
    modulus = 1_000_000_007
    previous = [1] * (nums[0] + 1)
    for index in range(1, len(nums)):
        for value in range(1, len(previous)):
            previous[value] = (previous[value] + previous[value - 1]) % modulus
        current = [0] * (nums[index] + 1)
        shift = min(0, nums[index - 1] - nums[index])
        for value in range(len(current)):
            limit = min(len(previous) - 1, value + shift)
            if limit >= 0:
                current[value] = previous[limit]
        previous = current
    return sum(previous) % modulus


class Solution:
    def countOfPairs(self, nums: list[int]) -> int:
        return solve(nums)
