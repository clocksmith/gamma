"""3939. Count Non Adjacent Subsets in a Rooted Tree
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/count-non-adjacent-subsets-in-a-rooted-tree/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3939.Count%20Non%20Adjacent%20Subsets%20in%20a%20Rooted%20Tree/README_EN.md
Complexity: O(n*k^2) time, O(n*k) space.
parent[i]<i enables reverse-index postorder. Empty subset subtracted. JS split-limb modular multiplication exact; native name pending.
"""

from __future__ import annotations

def solve(parent, nums, k):
    modulus = 1_000_000_007
    n = len(nums)
    skip = [[0] * k for _ in range(n)]
    take = [[0] * k for _ in range(n)]
    for node, value in enumerate(nums):
        skip[node][0] = 1
        take[node][value % k] = 1
    for child in range(n - 1, 0, -1):
        node = parent[child]
        new_skip = [0] * k
        new_take = [0] * k
        for first in range(k):
            for second in range(k):
                residue = (first + second) % k
                new_skip[residue] = (new_skip[residue] + skip[node][first] * (skip[child][second] + take[child][second])) % modulus
                new_take[residue] = (new_take[residue] + take[node][first] * skip[child][second]) % modulus
        skip[node], take[node] = new_skip, new_take
    return (skip[0][0] + take[0][0] - 1) % modulus
