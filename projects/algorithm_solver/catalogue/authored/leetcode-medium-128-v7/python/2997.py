"""2997. Minimum Number of Operations to Make Array XOR Equal to K: count the differing bits between the array xor and the target."""


def solve(nums: list[int], k: int) -> int:
    """O(n + log(M + 1)) time and O(1) auxiliary space on the bounded integer domain; inputs are read-only."""
    difference = k
    for value in nums:
        difference ^= value
    return difference.bit_count()


class Solution:
    def minOperations(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
