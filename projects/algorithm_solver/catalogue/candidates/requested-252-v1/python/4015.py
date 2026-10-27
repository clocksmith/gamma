"""4015. Weighted Sum of a Tree
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/weighted-sum-of-a-tree/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4015.Weighted%20Sum%20of%20a%20Tree/README_EN.md
Complexity: O(n) time and space.
Parent labels need not be topologically ordered. Iterative traversal avoids deep recursion. Total weighted sum <=1e6*n*(n+1)/2 <2^53. Native method unconfirmed.
"""

from __future__ import annotations

def solve(parent, nums):
    n = len(parent)
    children = [[] for _ in range(n)]
    for node in range(1, n):
        children[parent[node]].append(node)
    depth = [0] * n
    depth[0] = 1
    order = [0]
    height = 1
    for node in order:
        for child in children[node]:
            depth[child] = depth[node] + 1
            height = max(height, depth[child])
            order.append(child)
    return sum(value * (height - depth[node] + 1) for node, value in enumerate(nums))
