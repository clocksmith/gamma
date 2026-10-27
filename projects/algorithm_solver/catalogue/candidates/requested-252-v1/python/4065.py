"""4065. Rearrange Array by Removing Distinct Values
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/rearrange-array-by-removing-distinct-values/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4065.Rearrange%20Array%20by%20Removing%20Distinct%20Values/README_EN.md
Complexity: O(n+U log U) time, O(n+U) space.
Each round emits one occurrence of every remaining distinct value, ascending; exhausted values are removed from the active list. Original input is preserved.
"""

from __future__ import annotations
from collections import Counter

def solve(nums):
    counts = Counter(nums)
    active = sorted(counts)
    answer = []
    while active:
        following = []
        for value in active:
            answer.append(value)
            counts[value] -= 1
            if counts[value]:
                following.append(value)
        active = following
    return answer
