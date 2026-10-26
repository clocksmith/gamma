"""3668. Restore Finishing Order (Easy).

Specification: https://leetcode.com/problems/restore-finishing-order/description/
"""


def solve(order: list[int], friends: list[int]) -> list[int]:
    """O(n + f) expected time, O(f) space; preserve both input arrays."""
    friendIds = set(friends)
    result = []
    for participant in order:
        if participant in friendIds:
            result.append(participant)
    return result


class Solution:
    def recoverOrder(self, order: list[int], friends: list[int]) -> list[int]:
        return solve(order, friends)
