"""2149. Rearrange Array Elements by Sign (Medium).

Specification: https://leetcode.com/problems/rearrange-array-elements-by-sign/description/
"""


def solve(nums: list[int]) -> list[int]:
    positives = [x for x in nums if x > 0]
    negatives = [x for x in nums if x < 0]
    result = []
    for i, value in enumerate(positives):
        result.append(value)
        if i < len(negatives):
            result.append(negatives[i])
    result.extend(negatives[len(positives):])
    return result


class Solution:
    def rearrangeArray(self, nums: list[int]) -> list[int]:
        return solve(nums)
