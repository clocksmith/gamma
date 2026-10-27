"""4012. Count of Unfinished Tasks After Each Shift
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/count-of-unfinished-tasks-after-each-shift/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4012.Count%20of%20Unfinished%20Tasks%20After%20Each%20Shift/README_EN.md
Complexity: O(n + q log n) time, O(n) auxiliary space.
Completed shifts discard excess time rather than carrying a modulo remainder. Partial tasks count as unfinished; inputs preserved.
"""

from __future__ import annotations
from bisect import bisect_right

def solve(tasks, shifts):
    prefix = []
    total = 0
    for duration in tasks:
        total += duration
        prefix.append(total)
    answer = []
    spent = 0
    for duration in shifts:
        spent += duration
        if spent >= total:
            answer.append(0)
            spent = 0
        else:
            answer.append(len(tasks) - bisect_right(prefix, spent))
    return answer


class Solution:
    def countTasks(self, tasks, shifts):
        return solve(tasks, shifts)
