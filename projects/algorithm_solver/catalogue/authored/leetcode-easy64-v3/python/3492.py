"""3492. Maximum Containers on a Ship (Easy).

Specification: https://leetcode.com/problems/maximum-containers-on-a-ship/description/
"""


def solve(n: int, w: int, maxWeight: int) -> int:
    """O(1) time and space; both deck area and integer weight capacity limit the count."""
    return min(n * n, maxWeight // w)


class Solution:
    def maxContainers(self, n: int, w: int, maxWeight: int) -> int:
        return solve(n, w, maxWeight)
