"""4070. Minimum Rotations to Dial a Number I
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/minimum-rotations-to-dial-a-number-i/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4070.Minimum%20Rotations%20to%20Dial%20a%20Number%20I/README_EN.md
Complexity: O(len(s)) time, O(1) space.
Pointer starts at zero; clockwise/counterclockwise unit movement, no press cost. Input string preserved.
"""

from __future__ import annotations

def solve(s):
    previous = answer = 0
    for character in s:
        digit = ord(character)-48
        difference = abs(digit-previous)
        answer += min(difference, 10-difference)
        previous = digit
    return answer
