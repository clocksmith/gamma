"""350. Intersection of Two Arrays II."""
from collections import Counter

def solve(nums1: list[int], nums2: list[int]) -> list[int]:
    counts = Counter(nums1)
    result = []
    for value in nums2:
        if counts[value]:
            result.append(value)
            counts[value] -= 1
    return result

class Solution:
    def intersect(self, nums1: list[int], nums2: list[int]) -> list[int]:
        return solve(nums1, nums2)
