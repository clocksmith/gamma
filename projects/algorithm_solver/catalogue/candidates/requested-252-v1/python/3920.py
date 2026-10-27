"""3920. Maximize Fixed Points After Deletions
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/maximize-fixed-points-after-deletions/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3920.Maximize%20Fixed%20Points%20After%20Deletions/README_EN.md
Complexity: O(n log n) time, O(n) space.
0-based fixed points. Nonfixed retained elements may fill gaps. Batches prevent equal-value fixed points. Native name pending.
"""

from __future__ import annotations

def solve(nums):
    # A fixed point (i,v) needs i-v deletions before it. Along a valid
    # chain, v strictly increases and i-v cannot decrease.
    candidates = sorted((value, index - value) for index, value in enumerate(nums) if value <= index)
    tree = [0] * (len(nums) + 2)
    answer = 0
    start = 0
    while start < len(candidates):
        end = start
        pending = []
        while end < len(candidates) and candidates[end][0] == candidates[start][0]:
            position = candidates[end][1] + 1
            best = 0
            cursor = position
            while cursor:
                best = max(best, tree[cursor])
                cursor -= cursor & -cursor
            pending.append((position, best + 1))
            answer = max(answer, best + 1)
            end += 1
        for position, best in pending:
            while position < len(tree):
                tree[position] = max(tree[position], best)
                position += position & -position
        start = end
    return answer
