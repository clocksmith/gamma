"""4001. Aggregate Two Time Series
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/aggregate-two-time-series/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4001.Aggregate%20Two%20Time%20Series/README_EN.md
Complexity: O(n+m) time, O(1) auxiliary space excluding output.
Missing timestamps take the NEXT available value, not the previous value. Inputs preserved; native method unconfirmed.
"""

from __future__ import annotations

def solve(series1, series2):
    i = j = 0
    answer = []
    while i < len(series1) or j < len(series2):
        t1 = series1[i][0] if i < len(series1) else float('inf')
        t2 = series2[j][0] if j < len(series2) else float('inf')
        timestamp = min(t1, t2)
        value = (series1[i][1] if i < len(series1) else 0) + (series2[j][1] if j < len(series2) else 0)
        answer.append([timestamp, value])
        i += int(t1 == timestamp)
        j += int(t2 == timestamp)
    return answer
