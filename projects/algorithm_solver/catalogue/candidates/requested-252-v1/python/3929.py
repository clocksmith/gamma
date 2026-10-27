"""3929. Minimum Partition Score II
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/minimum-partition-score-ii/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3929.Minimum%20Partition%20Score%20II/README_EN.md
Complexity: O(n log(S^2)) arithmetic operations, O(n) space; S=sum(nums).
Positive nums<=1000 and n<=50000. Exact BigInt hull comparisons/penalty arithmetic; final <=1.251e15 Number. Lagrangian convex-count optimization; native entry pending. Not benchmarked.
"""

from __future__ import annotations

def solve(nums, k):
    prefix = [0]
    for value in nums:
        prefix.append(prefix[-1] + value)
    total = prefix[-1]
    if k == 1:
        return total * (total + 1) // 2
    if k == len(nums):
        return sum(value * (value + 1) // 2 for value in nums)
    def penalized(penalty):
        # Lines are (slope, intercept, segment_count). Slopes decrease,
        # queries increase. Keep collinear lines for count tie-breaking.
        hull = [(0, 0, 0)]
        head = 0
        cost = count = 0
        for value in prefix[1:]:
            best = hull[head][0] * value + hull[head][1]
            count = hull[head][2]
            while head + 1 < len(hull):
                following = hull[head + 1][0] * value + hull[head + 1][1]
                if following > best:
                    break
                head += 1
                if following < best:
                    best, count = following, hull[head][2]
                else:
                    count = max(count, hull[head][2])
            cost = value * value + penalty + best
            count += 1
            line = (-2 * value, cost + value * value, count)
            while len(hull) - head >= 2:
                first, second = hull[-2], hull[-1]
                if (second[1] - first[1]) * (second[0] - line[0]) > (line[1] - second[1]) * (first[0] - second[0]):
                    hull.pop()
                else:
                    break
            hull.append(line)
        return cost, count
    # Squared interval-sum costs are Monge, with convex optimal cost
    # as a function of segment count. Largest penalty retaining >=k
    # segments supports the exact-k optimum; ties favor more segments.
    low, high = 0, total * total + 1
    while low + 1 < high:
        middle = (low + high) // 2
        if penalized(middle)[1] >= k:
            low = middle
        else:
            high = middle
    cost, _ = penalized(low)
    return (cost - low * k + total) // 2
