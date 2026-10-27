"""3991. Sort Array Using Prefix Reversals
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/sort-array-using-prefix-reversals/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3991.Sort%20Array%20Using%20Prefix%20Reversals/README_EN.md
Complexity: O(n!*|pre|*n) time, O(n!*n) space; n<=8.
BFS over permutations, exact string encoding is unambiguous for digits 0..7. Inputs preserved.
"""

from __future__ import annotations
from collections import deque

def solve(nums, pre):
    start, target = tuple(nums), tuple(range(len(nums)))
    if start == target:
        return 0
    lengths = [length for length in pre if length > 1]
    seen = {start}
    queue = deque([(start, 0)])
    while queue:
        state, distance = queue.popleft()
        for length in lengths:
            following = state[:length][::-1] + state[length:]
            if following == target:
                return distance + 1
            if following not in seen:
                seen.add(following)
                queue.append((following, distance + 1))
    return -1


class Solution:
    def sortArray(self, nums, pre):
        return solve(nums, pre)
