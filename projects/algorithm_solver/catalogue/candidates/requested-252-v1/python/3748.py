"""3748. Count Stable Subarrays
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/count-stable-subarrays/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3700-3799/3748.Count%20Stable%20Subarrays/README_EN.md
Complexity: O(n+q) time; O(n+q) space including returned answers.
Stable means nondecreasing; queries do not mutate input. Counts fit Number.
"""

from __future__ import annotations

def solve(nums, queries):
    n = len(nums)
    starts, ends, prefix = [0] * n, [0] * n, [0] * (n + 1)
    for index in range(n):
        starts[index] = starts[index - 1] if index and nums[index - 1] <= nums[index] else index
        prefix[index + 1] = prefix[index] + index - starts[index] + 1
    for index in range(n - 1, -1, -1):
        ends[index] = ends[index + 1] if index + 1 < n and nums[index] <= nums[index + 1] else index
    return [prefix[right + 1] - prefix[left] - (left - starts[left]) * (min(right, ends[left]) - left + 1) for left, right in queries]


class Solution:
    def countStableSubarrays(self, nums, queries):
        return solve(nums, queries)
