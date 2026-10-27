"""3923. Minimum Generations to Target Point
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/minimum-generations-to-target-point/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3923.Minimum%20Generations%20to%20Target%20Point/README_EN.md
Complexity: O(U^2) time, O(U) space, U <= 7^3.
Generations are simultaneous. Only pairs involving newly available points need processing. Distinct coordinate pairs, no self-pairing. Native name pending.
"""

from __future__ import annotations

def solve(points, target):
    known = [tuple(point) for point in points]
    seen = set(known)
    destination = tuple(target)
    if destination in seen:
        return 0
    first_new = 0
    generation = 0
    while first_new < len(known):
        pending = set()
        old_size = len(known)
        for first in range(first_new, old_size):
            for second in range(first):
                point = tuple((known[first][axis] + known[second][axis]) // 2 for axis in range(3))
                if point not in seen:
                    pending.add(point)
        generation += 1
        if destination in pending:
            return generation
        first_new = old_size
        known.extend(sorted(pending))
        seen.update(pending)
    return -1
