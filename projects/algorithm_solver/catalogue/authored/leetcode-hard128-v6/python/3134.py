"""3134. Find the Median of the Uniqueness Array.

Binary search the lower median using counts of windows with at most d distinct values; O(n log n) expected time, O(n) space. Inputs are preserved.
"""

def solve(nums: list[int]) -> int:
    n = len(nums)
    target = (n * (n + 1) // 2 + 1) // 2

    def enough(limit):
        counts = {}
        left = total = 0
        for right, value in enumerate(nums):
            counts[value] = counts.get(value, 0) + 1
            while len(counts) > limit:
                old = nums[left]
                counts[old] -= 1
                if not counts[old]:
                    del counts[old]
                left += 1
            total += right - left + 1
            if total >= target:
                return True
        return False

    low, high = 1, len(set(nums))
    while low < high:
        middle = (low + high) // 2
        if enough(middle):
            high = middle
        else:
            low = middle + 1
    return low


class Solution:
    def medianOfUniquenessArray(self, nums: list[int]) -> int:
        return solve(nums)
