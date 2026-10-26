"""2261. K Divisible Elements Subarrays: insert eligible subarrays into a value trie and count only newly created prefixes."""


def solve(nums: list[int], k: int, p: int) -> int:
    """O(n^2) expected time and O(n^2) auxiliary space; inputs are read-only."""
    root = {}
    distinct = 0
    for left in range(len(nums)):
        node = root
        divisible = 0
        for right in range(left, len(nums)):
            value = nums[right]
            divisible += value % p == 0
            if divisible > k:
                break
            if value not in node:
                node[value] = {}
                distinct += 1
            node = node[value]
    return distinct


class Solution:
    def countDistinct(self, nums: list[int], k: int, p: int) -> int:
        return solve(nums, k, p)
