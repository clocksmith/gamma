"""1589. Maximum Sum Obtained of Any Permutation: pair the largest values with the most-requested positions using a difference array."""


def solve(nums: list[int], requests: list[list[int]]) -> int:
    """O(n log(n + 1) + q) time and O(n) auxiliary space; inputs are read-only."""
    modulus = 1_000_000_007
    difference = [0] * (len(nums) + 1)
    for left, right in requests:
        difference[left] += 1
        difference[right + 1] -= 1
    frequencies = []
    active = 0
    for index in range(len(nums)):
        active += difference[index]
        frequencies.append(active)
    frequencies.sort()
    total = 0
    for value, count in zip(sorted(nums), frequencies):
        total = (total + value * count) % modulus
    return total


class Solution:
    def maxSumRangeQuery(self, nums: list[int], requests: list[list[int]]) -> int:
        return solve(nums, requests)
