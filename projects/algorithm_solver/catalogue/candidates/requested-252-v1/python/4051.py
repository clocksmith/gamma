"""4051. Count Subarrays with Distant Sums
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/count-subarrays-with-distant-sums/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4051.Count%20Subarrays%20with%20Distant%20Sums/README_EN.md
Complexity: O(n log n) time, O(n) space.
Subtract strictly-near sums from all nonempty subarrays. k=0 returns all subarrays without overlapping-boundary counting. Signed prefix sums remain exact within stated JS Number range. Inputs preserved.
"""

from __future__ import annotations
from bisect import bisect_left, bisect_right

def solve(nums, goal, k):
    n = len(nums)
    answer = n*(n+1)//2
    if k == 0:
        return answer
    prefixes = [0]
    for value in nums:
        prefixes.append(prefixes[-1]+value)
    coordinates = sorted(set(prefixes))
    tree = [0]*(len(coordinates)+1)
    def count(end):
        total = 0
        while end:
            total += tree[end]
            end -= end & -end
        return total
    for value in prefixes:
        left = bisect_right(coordinates, value-goal-k)
        right = bisect_left(coordinates, value-goal+k)
        answer -= count(right)-count(left)
        p = bisect_left(coordinates, value)+1
        while p < len(tree):
            tree[p] += 1
            p += p & -p
    return answer
