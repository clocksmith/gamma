"""4005. Minimum Operations to Make Array Equal III
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/minimum-operations-to-make-array-equal-iii/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4005.Minimum%20Operations%20to%20Make%20Array%20Equal%20III/README_EN.md
Complexity: O(n + U*log M) expected time, O(U) space; M=max(nums), U=distinct values.
A new common multiple gives n operations. An improving existing target t>1 must have frequency(t)>count(incomparable values). Cancel incomparable pairs; every improving target survives in a divisibility chain of at most floor(log2 M)+1 values. Direct comparable changes cost one, incomparable changes two via a common multiple. Division to 1 is forbidden. Native method unconfirmed.
"""

from __future__ import annotations
from collections import Counter

def solve(nums):
    frequencies = Counter(nums)
    if len(frequencies) == 1:
        return 0
    survivors = {}
    for value, amount in frequencies.items():
        while amount:
            conflict = next((other for other in survivors if value % other and other % value), None)
            if conflict is None:
                survivors[value] = survivors.get(value, 0) + amount
                break
            removed = min(amount, survivors[conflict])
            amount -= removed
            survivors[conflict] -= removed
            if survivors[conflict] == 0:
                del survivors[conflict]
    n = len(nums)
    answer = n
    for target in survivors:
        if target == 1:
            continue
        cost = n - frequencies[target]
        for value, amount in frequencies.items():
            if target % value and value % target:
                cost += amount
                if cost >= answer:
                    break
        answer = min(answer, cost)
    return answer
