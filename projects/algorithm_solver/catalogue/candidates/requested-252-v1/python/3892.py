"""3892. Minimum Operations to Achieve At Least K Peaks
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/minimum-operations-to-achieve-at-least-k-peaks/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3800-3899/3892.Minimum%20Operations%20to%20Achieve%20At%20Least%20K%20Peaks/README_EN.md
Complexity: O(n*k) time; O(n+k) space.
Circular nonadjacent peak selection. 2 <= n <= 5000. Native judge method not established; canonical solve only.
"""

from __future__ import annotations

def solve(nums, k):
    n = len(nums)
    if k == 0:
        return 0
    if k > n // 2:
        return -1
    costs = [max(0, max(nums[(i - 1) % n], nums[(i + 1) % n]) + 1 - nums[i]) for i in range(n)]
    def chain(left, right, needed):
        if needed == 0:
            return 0
        if needed > (max(0, right - left + 1) + 1) // 2:
            return float('inf')
        skip = [float('inf')] * (needed + 1)
        take = skip.copy()
        skip[0] = 0
        for index in range(left, right + 1):
            next_skip = [min(a, b) for a, b in zip(skip, take)]
            next_take = [float('inf')] * (needed + 1)
            for count in range(1, needed + 1):
                next_take[count] = skip[count - 1] + costs[index]
            skip, take = next_skip, next_take
        return min(skip[needed], take[needed])
    return min(chain(1, n - 1, k), costs[0] + chain(2, n - 2, k - 1))
