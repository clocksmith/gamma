"""3699. Number of ZigZag Arrays I
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/number-of-zigzag-arrays-i/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3600-3699/3699.Number%20of%20ZigZag%20Arrays%20I/README_EN.md
Complexity: O(n(r-l+1)) time; O(r-l+1) space.
Strict alternating comparisons; modulus 1e9+7; n >= 3 as specified.
"""

from __future__ import annotations

def solve(n, l, r):
    modulus = 1_000_000_007
    width = r - l + 1
    up = [1] * width
    down = [1] * width
    for _ in range(n - 1):
        next_up, next_down = [0] * width, [0] * width
        running = 0
        for value in range(width):
            next_up[value] = running
            running = (running + down[value]) % modulus
        running = 0
        for value in range(width - 1, -1, -1):
            next_down[value] = running
            running = (running + up[value]) % modulus
        up, down = next_up, next_down
    return sum(up + down) % modulus


class Solution:
    def zigZagArrays(self, n, l, r):
        return solve(n, l, r)
