"""15. 3Sum (Medium).

Specification: https://leetcode.com/problems/3sum/description/
"""


def solve(nums: list[int]) -> list[list[int]]:
    ordered = sorted(nums)
    result = []
    for i in range(len(ordered) - 2):
        if i > 0 and ordered[i] == ordered[i - 1]:
            continue
        left, right = i + 1, len(ordered) - 1
        while left < right:
            total = ordered[i] + ordered[left] + ordered[right]
            if total == 0:
                result.append([ordered[i], ordered[left], ordered[right]])
                while left < right and ordered[left] == ordered[left + 1]:
                    left += 1
                while left < right and ordered[right] == ordered[right - 1]:
                    right -= 1
                left += 1
                right -= 1
            elif total < 0:
                left += 1
            else:
                right -= 1
    return result


class Solution:
    def threeSum(self, nums: list[int]) -> list[list[int]]:
        return solve(nums)
