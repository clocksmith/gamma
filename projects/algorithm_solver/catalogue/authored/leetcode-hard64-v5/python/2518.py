"""2518. Number of Great Partitions. Subtract small-sum subsets from all ordered bipartitions."""


def solve(nums: list[int], k: int) -> int:
    """O(n*k) time and O(k) space. Inputs are preserved."""
    modulus = 1_000_000_007
    if sum(nums) < 2 * k:
        return 0
    counts = [0] * k
    counts[0] = 1
    for value in nums:
        for total in range(k - 1, value - 1, -1):
            counts[total] = (counts[total] + counts[total - value]) % modulus
    return (pow(2, len(nums), modulus) - 2 * sum(counts)) % modulus


class Solution:
    def countPartitions(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
