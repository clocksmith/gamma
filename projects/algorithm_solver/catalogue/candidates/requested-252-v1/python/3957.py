"""3957. Maximum Sum of M Non-Overlapping Subarrays II
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/maximum-sum-of-m-non-overlapping-subarrays-ii/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3957.Maximum%20Sum%20of%20M%20Non-Overlapping%20Subarrays%20II/README_EN.md
Complexity: O(n*min(m,floor(n/l))) time and O(n) space; exact layer DP with a sliding maximum.
At least one subarray is required, including all-negative input. Inputs preserved. Native judge method pending. PERFORMANCE LIMITATION: quadratic worst case at n=100000; full-size time-limit suitability is not established. This is a complete exact algorithm, not a claimed fast solution to the largest instances.
"""

from __future__ import annotations
from collections import deque

def solve(nums, m, l, r):
    n = len(nums)
    prefix = [0]
    for value in nums:
        prefix.append(prefix[-1] + value)
    negative = float('-inf')
    # Exact t-segment layers. The zero-segment layer alone permits the empty set.
    previous = [0] * (n + 1)
    answer = negative
    for count in range(1, min(m, n // l) + 1):
        current = [negative] * (n + 1)
        queue = deque()
        for end in range(1, n + 1):
            start = end - l
            if start >= 0 and previous[start] != negative:
                value = previous[start] - prefix[start]
                while queue and queue[-1][1] <= value:
                    queue.pop()
                queue.append((start, value))
            while queue and queue[0][0] < end - r:
                queue.popleft()
            current[end] = current[end - 1]
            if queue:
                current[end] = max(current[end], prefix[end] + queue[0][1])
        answer = max(answer, current[n])
        previous = current
    return answer
