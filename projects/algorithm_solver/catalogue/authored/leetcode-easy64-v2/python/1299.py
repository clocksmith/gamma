"""1299. Replace Elements with Greatest Element on Right Side (Easy).

Specification: https://leetcode.com/problems/replace-elements-with-greatest-element-on-right-side/description/
"""


def solve(arr: list[int]) -> list[int]:
    """O(n) time, O(n) output space; preserve arr."""
    result = [0] * len(arr)
    greatest = -1
    for index in range(len(arr) - 1, -1, -1):
        result[index] = greatest
        greatest = max(greatest, arr[index])
    return result


class Solution:
    def replaceElements(self, arr: list[int]) -> list[int]:
        return solve(arr)
