"""3648. Minimum Sensors to Cover Grid.

Specification: https://leetcode.com/problems/minimum-sensors-to-cover-grid/description/
Authored candidate; not executed, syntax-checked, tested, or Gamma-qualified.
O(1) time and space; each sensor covers Chebyshev distance at most k.
Inputs are not modified.
"""

def solve(n, m, k):
    width = 2 * k + 1
    return ((n + width - 1) // width) * ((m + width - 1) // width)


class Solution:
    def minSensors(self, n, m, k):
        return solve(n, m, k)
