"""205. Isomorphic Strings (Easy).

Specification: https://leetcode.com/problems/isomorphic-strings/description/
"""


def solve(s: str, t: str) -> bool:
    """O(n) time, O(a) space for distinct characters; enforce a bijection on ASCII input."""
    if len(s) != len(t):
        return False
    forward = {}
    backward = {}
    for first, second in zip(s, t):
        if first in forward and forward[first] != second:
            return False
        if second in backward and backward[second] != first:
            return False
        forward[first] = second
        backward[second] = first
    return True


class Solution:
    def isIsomorphic(self, s: str, t: str) -> bool:
        return solve(s, t)
