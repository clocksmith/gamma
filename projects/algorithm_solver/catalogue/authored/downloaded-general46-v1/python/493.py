"""493. Reverse Pairs (Hard).

Specification: https://leetcode.com/problems/reverse-pairs/description/
"""


def solve(nums: list[int]) -> int:
    count = 0

    def merge_sort(values):
        nonlocal count
        if len(values) <= 1:
            return values
        mid = len(values) // 2
        left = merge_sort(values[:mid])
        right = merge_sort(values[mid:])
        j = 0
        for value in left:
            while j < len(right) and value > 2 * right[j]:
                j += 1
            count += j
        merged = []
        i = 0
        k = 0
        while i < len(left) and k < len(right):
            if left[i] <= right[k]:
                merged.append(left[i])
                i += 1
            else:
                merged.append(right[k])
                k += 1
        merged.extend(left[i:])
        merged.extend(right[k:])
        return merged

    merge_sort(nums[:])
    return count


class Solution:
    def reversePairs(self, nums: list[int]) -> int:
        return solve(nums)
