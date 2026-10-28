"""1427. Perform String Shifts (Easy).

Specification: https://leetcode.com/problems/perform-string-shifts/description/
"""


def solve(s, shift):
    if not s:
        return s
    net = 0
    for direction, amount in shift:
        net += amount if direction == 1 else -amount
    net %= len(s)
    if net == 0:
        return s
    return s[-net:] + s[:-net]


class Solution:
    def stringShift(self, s, shift):
        return solve(s, shift)
