"""324. Wiggle Sort II (Medium).

Specification: https://leetcode.com/problems/wiggle-sort-ii/description/
"""


def solve(nums: list[int]) -> list[int]:
    ordered = sorted(nums)
    n = len(ordered)
    small = ordered[:(n + 1) // 2][::-1]
    large = ordered[(n + 1) // 2:][::-1]
    result = []
    for i in range(n):
        result.append(small[i // 2] if i % 2 == 0 else large[i // 2])
    return result


class Solution:
    def wiggleSort(self, nums: list[int]) -> None:
        ordered = sorted(nums)
        low, high = (len(nums) - 1) // 2, len(nums) - 1
        for index in range(len(nums)):
            if index % 2:
                nums[index] = ordered[high]
                high -= 1
            else:
                nums[index] = ordered[low]
                low -= 1
