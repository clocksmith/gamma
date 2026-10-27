"""3934. Smallest Unique Subarray
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/smallest-unique-subarray/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3934.Smallest%20Unique%20Subarray/README_EN.md
Complexity: O(n log^2 n) comparison-sort time, O(n) space.
Exact suffix ranks and Kasai LCP, no probabilistic hash. Inputs preserved; performance not measured.
"""

from __future__ import annotations

def solve(nums):
    n = len(nums)
    values = {value: index for index, value in enumerate(sorted(set(nums)))}
    rank = [values[value] for value in nums]
    suffixes = list(range(n))
    width = 1
    while width < n:
        suffixes.sort(key=lambda index: (rank[index], rank[index + width] if index + width < n else -1))
        next_rank = [0] * n
        for index in range(1, n):
            previous, current = suffixes[index - 1], suffixes[index]
            previous_key = (rank[previous], rank[previous + width] if previous + width < n else -1)
            current_key = (rank[current], rank[current + width] if current + width < n else -1)
            next_rank[current] = next_rank[previous] + int(previous_key != current_key)
        rank = next_rank
        if rank[suffixes[-1]] == n - 1:
            break
        width *= 2
    position = [0] * n
    for index, start in enumerate(suffixes):
        position[start] = index
    lcp = [0] * n
    common = 0
    for start in range(n):
        index = position[start]
        if index == 0:
            common = 0
            continue
        previous = suffixes[index - 1]
        while start + common < n and previous + common < n and nums[start + common] == nums[previous + common]:
            common += 1
        lcp[index] = common
        common = max(0, common - 1)
    answer = n
    for index, start in enumerate(suffixes):
        needed = 1 + max(lcp[index], lcp[index + 1] if index + 1 < n else 0)
        if needed <= n - start:
            answer = min(answer, needed)
    return answer


class Solution:
    def smallestUniqueSubarray(self, nums):
        return solve(nums)
