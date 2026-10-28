"""1526. Minimum Number of Increments on Subarrays to Form a Target Array (Hard).

Specification: https://leetcode.com/problems/minimum-number-of-increments-on-subarrays-to-form-a-target-array/description/
"""


def solve(target: list[int]) -> int:
    operations = target[0]
    for i in range(1, len(target)):
        if target[i] > target[i - 1]:
            operations += target[i] - target[i - 1]
    return operations


class Solution:
    def minNumberOperations(self, target: list[int]) -> int:
        return solve(target)
