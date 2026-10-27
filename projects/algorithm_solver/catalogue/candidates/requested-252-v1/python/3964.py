"""3964. Minimum Lights to Illuminate a Road
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/minimum-lights-to-illuminate-a-road/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3964.Minimum%20Lights%20to%20Illuminate%20a%20Road/README_EN.md
Complexity: O(n) time and space.
Greedily cover the first uncovered cell using a new lamp as far right as possible. Existing lights are retained; inputs preserved.
"""

from __future__ import annotations

def solve(lights):
    n = len(lights)
    difference = [0] * (n + 1)
    for index, radius in enumerate(lights):
        if radius:
            difference[max(0, index - radius)] += 1
            difference[min(n, index + radius + 1)] -= 1
    coverage = 0
    added_until = -1
    answer = 0
    for index in range(n):
        coverage += difference[index]
        if coverage == 0 and index > added_until:
            answer += 1
            added_until = min(n - 1, index + 2)
    return answer


class Solution:
    def minLights(self, lights):
        return solve(lights)
