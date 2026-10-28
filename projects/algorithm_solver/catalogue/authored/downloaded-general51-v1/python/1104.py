"""1104. Path In Zigzag Labelled Binary Tree (Medium).

Specification: https://leetcode.com/problems/path-in-zigzag-labelled-binary-tree/description/
"""


import math


def _level_of(label):
    return int(math.log2(label))


def solve(label: int) -> list[int]:
    result = []
    current = label
    while current >= 1:
        result.append(current)
        if current == 1:
            break
        level = _level_of(current)
        normal = 3 * (2 ** level) - 1 - current if level % 2 == 1 else current
        parent_normal = normal // 2
        parent_level = level - 1
        current = 3 * (2 ** parent_level) - 1 - parent_normal if parent_level % 2 == 1 else parent_normal
    return result[::-1]


class Solution:
    def pathInZigZagTree(self, label: int) -> list[int]:
        return solve(label)
