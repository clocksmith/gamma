"""2200. Find All K-Distant Indices in an Array (Easy).

Specification: https://leetcode.com/problems/find-all-k-distant-indices-in-an-array/description/
"""


def solve(nums: list[int], key: int, k: int) -> list[int]:
    """O(n) time and output space; append each covered index once by merging increasing intervals."""
    result = []
    next_index = 0
    for index, value in enumerate(nums):
        if value != key:
            continue
        start = max(next_index, index - k, 0)
        end = min(len(nums) - 1, index + k)
        result.extend(range(start, end + 1))
        next_index = end + 1
    return result


class Solution:
    def findKDistantIndices(self, nums: list[int], key: int, k: int) -> list[int]:
        return solve(nums, key, k)
