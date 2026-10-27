"""4045. Count Robot Groups
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/count-robot-groups/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4045.Count%20Robot%20Groups/README_EN.md
Complexity: O(n) time, O(n) space.
Collapse entire connected runs at time zero to their rightmost representative. Thereafter speeds can only decrease through catch-up merges. A representative faster than a suffix minimum eventually joins; equal speeds with a positive initial gap remain separate. Inputs preserved.
"""

from __future__ import annotations

def solve(position, speed, distance):
    # Simultaneous time-zero connectivity is resolved before later collisions.
    representatives = []
    for i in range(len(position)):
        if i + 1 == len(position) or position[i+1] - position[i] > distance:
            representatives.append(speed[i])
    groups = 0
    minimum = float('inf')
    for velocity in reversed(representatives):
        if velocity <= minimum:
            groups += 1
            minimum = velocity
    return groups
