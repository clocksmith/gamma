"""3691. Maximum Total Subarray Value II
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/maximum-total-subarray-value-ii/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3600-3699/3691.Maximum%20Total%20Subarray%20Value%20II/README_EN.md
Complexity: O((n+k) log n) time; O(n log n) space.
Inputs preserved. Distinct (left,right) subarrays; sum <= 1e14 is exact as a JavaScript Number.
"""

from __future__ import annotations
from heapq import heapify, heappop, heappush

def solve(nums, k):
    n = len(nums)
    maximum, minimum = [list(nums)], [list(nums)]
    width = 1
    while width * 2 <= n:
        previous_max, previous_min = maximum[-1], minimum[-1]
        maximum.append([max(previous_max[i], previous_max[i + width]) for i in range(n - 2 * width + 1)])
        minimum.append([min(previous_min[i], previous_min[i + width]) for i in range(n - 2 * width + 1)])
        width *= 2
    def value(left, right):
        power = (right - left + 1).bit_length() - 1
        offset = right - (1 << power) + 1
        return max(maximum[power][left], maximum[power][offset]) - min(minimum[power][left], minimum[power][offset])
    heap = [(-value(left, n - 1), left, n - 1) for left in range(n)]
    heapify(heap)
    answer = 0
    for _ in range(k):
        negative, left, right = heappop(heap)
        answer -= negative
        if right > left:
            heappush(heap, (-value(left, right - 1), left, right - 1))
    return answer


class Solution:
    def maxTotalValue(self, nums, k):
        return solve(nums, k)
