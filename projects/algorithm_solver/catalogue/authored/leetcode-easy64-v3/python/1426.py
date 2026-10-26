"""1426. Counting Elements (Easy).

Specification: https://leetcode.com/problems/counting-elements/description/
"""


def solve(arr: list[int]) -> int:
    """O(n) expected time, O(n) space; count occurrences and preserve arr."""
    present = set(arr)
    result = 0
    for value in arr:
        if value + 1 in present:
            result += 1
    return result


class Solution:
    def countElements(self, arr: list[int]) -> int:
        return solve(arr)
