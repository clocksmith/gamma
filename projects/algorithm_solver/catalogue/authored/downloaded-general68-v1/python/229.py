"""229. Majority Element II (Medium).

Specification: https://leetcode.com/problems/majority-element-ii/description/
"""


def solve(nums: list[int]) -> list[int]:
    count1 = 0
    count2 = 0
    candidate1 = None
    candidate2 = None
    for value in nums:
        if candidate1 == value:
            count1 += 1
        elif candidate2 == value:
            count2 += 1
        elif count1 == 0:
            candidate1, count1 = value, 1
        elif count2 == 0:
            candidate2, count2 = value, 1
        else:
            count1 -= 1
            count2 -= 1
    result = []
    for candidate in (candidate1, candidate2):
        if candidate is not None and nums.count(candidate) > len(nums) // 3:
            result.append(candidate)
    return sorted(result)


class Solution:
    def majorityElement(self, nums: list[int]) -> list[int]:
        return solve(nums)
