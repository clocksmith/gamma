"""331. Verify Preorder Serialization of a Binary Tree (Medium).

Specification: https://leetcode.com/problems/verify-preorder-serialization-of-a-binary-tree/description/
"""


def solve(preorder: str) -> bool:
    tokens = preorder.split(',')
    slots = 1
    for token in tokens:
        slots -= 1
        if slots < 0:
            return False
        if token != '#':
            slots += 2
    return slots == 0


class Solution:
    def isValidSerialization(self, preorder: str) -> bool:
        return solve(preorder)
