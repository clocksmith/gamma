"""3965. Finish Time of Tasks I
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/finish-time-of-tasks-i/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3965.Finish%20Time%20of%20Tasks%20I/README_EN.md
Complexity: O(n) time and space, iterative traversal.
Edges are directed parent-child pairs as stated. Every task finish is guaranteed below 2^53; evaluate latest+(latest-earliest)+base, not an unsafe doubled intermediate. Inputs preserved; native method pending.
"""

from __future__ import annotations

def solve(n, edges, baseTime):
    children = [[] for _ in range(n)]
    for parent, child in edges:
        children[parent].append(child)
    order = [0]
    for node in order:
        order.extend(children[node])
    finish = baseTime.copy()
    for node in reversed(order):
        if children[node]:
            earliest = min(finish[child] for child in children[node])
            latest = max(finish[child] for child in children[node])
            finish[node] = latest + (latest - earliest) + baseTime[node]
    return finish[0]
