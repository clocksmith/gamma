"""3890. Integers With Multiple Sum of Two Cubes
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/integers-with-multiple-sum-of-two-cubes/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3800-3899/3890.Integers%20With%20Multiple%20Sum%20of%20Two%20Cubes/README_EN.md
Complexity: O(n^(2/3) + g log g) time; O(n^(2/3)) space.
1 <= n <= 1e9. Counts unordered positive cube pairs; inputs preserved.
"""

from __future__ import annotations

def solve(n):
    cubes = []
    value = 1
    while value * value * value <= n:
        cubes.append(value * value * value)
        value += 1
    counts = {}
    for first, cube in enumerate(cubes):
        for second in range(first, len(cubes)):
            total = cube + cubes[second]
            if total > n:
                break
            counts[total] = counts.get(total, 0) + 1
    return sorted(value for value, count in counts.items() if count >= 2)


class Solution:
    def findGoodIntegers(self, n):
        return solve(n)
