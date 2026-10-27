"""3944. Minimum Operations to Make Array Modulo Alternating II
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/minimum-operations-to-make-array-modulo-alternating-ii/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3944.Minimum%20Operations%20to%20Make%20Array%20Modulo%20Alternating%20II/README_EN.md
Complexity: O(n+k) time, O(k) auxiliary space.
Circular residue distances; two distinct targets. Inputs preserved. All totals safely bounded for n,k<=1e5; native name pending for II.
"""

from __future__ import annotations

def solve(nums, k):
    frequency = [[0] * k for _ in range(2)]
    for index, value in enumerate(nums):
        frequency[index % 2][value % k] += 1
    def costs(counts):
        repeated = counts + counts
        prefix_count = [0]
        prefix_weight = [0]
        for index, count in enumerate(repeated):
            prefix_count.append(prefix_count[-1] + count)
            prefix_weight.append(prefix_weight[-1] + index * count)
        result = []
        for residue in range(k):
            middle = residue + k // 2 + 1
            end = residue + k
            forward_count = prefix_count[middle] - prefix_count[residue]
            forward_sum = prefix_weight[middle] - prefix_weight[residue]
            backward_count = prefix_count[end] - prefix_count[middle]
            backward_sum = prefix_weight[end] - prefix_weight[middle]
            result.append(forward_sum - residue * forward_count + end * backward_count - backward_sum)
        return result
    even, odd = costs(frequency[0]), costs(frequency[1])
    first = min(range(k), key=lambda index: odd[index])
    second = min(odd[index] for index in range(k) if index != first)
    return min(cost + (second if index == first else odd[first]) for index, cost in enumerate(even))
