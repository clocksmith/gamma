"""4009. Minimum Possible Maximum Waiting Time
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/minimum-possible-maximum-waiting-time/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4009.Minimum%20Possible%20Maximum%20Waiting%20Time/README_EN.md
Complexity: O(n*F*D^2) time, O(F*D^2) space, F<=50 and D<=20.
Layered DP maximizes served prefix before minimizing maximum wait. Residual busy times are relative to the previous start, not absolute arrival zero. One fuel coordinate follows from consumed prefix demand. Inputs preserved; native method unconfirmed.
"""

from __future__ import annotations

def solve(demand, fuel):
    states = {(0, 0, 0): 0}
    consumed = 0
    served = 0
    for amount in demand:
        following = {}
        for (used0, busy0, busy1), worst in states.items():
            used1 = consumed - used0
            if used0 + amount <= fuel[0]:
                key = (used0 + amount, amount, max(0, busy1 - busy0))
                cost = max(worst, busy0)
                following[key] = min(following.get(key, float('inf')), cost)
            if used1 + amount <= fuel[1]:
                key = (used0, max(0, busy0 - busy1), amount)
                cost = max(worst, busy1)
                following[key] = min(following.get(key, float('inf')), cost)
        if not following:
            break
        states = following
        consumed += amount
        served += 1
    return min(states.values()) if served else -1
