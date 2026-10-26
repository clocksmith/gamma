"""1346. Check If N and Its Double Exist (Easy).

Specification: https://leetcode.com/problems/check-if-n-and-its-double-exist/description/
"""


def solve(arr: list[int]) -> bool:
    """O(n) expected time, O(n) space; query only earlier elements so indices remain distinct."""
    seen = set()
    for value in arr:
        if 2 * value in seen or (value % 2 == 0 and value // 2 in seen):
            return True
        seen.add(value)
    return False


class Solution:
    def checkIfExist(self, arr: list[int]) -> bool:
        return solve(arr)
