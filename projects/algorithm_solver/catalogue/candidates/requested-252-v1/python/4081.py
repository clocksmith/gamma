"""4081. Prime Subset Selection II
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/prime-subset-selection-ii/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4081.Prime%20Subset%20Selection%20II/README_EN.md
Complexity: O(n log log n + pi(n)*s) time, O(pi(n)*s+n) space.
Suffix 0/1 knapsack stores minimum cardinality at each exact sum. First choose the largest reachable sum, then greedily take the smallest prime whenever the optimal remaining cardinality is achievable using larger primes. This enforces all three priorities without reusing a prime. n,s<=1000.
"""

from __future__ import annotations

def solve(n, s):
    limit = min(n, s)
    if limit < 2:
        return []
    prime = [True]*(limit+1)
    prime[0] = prime[1] = False
    divisor = 2
    while divisor*divisor <= limit:
        if prime[divisor]:
            for multiple in range(divisor*divisor, limit+1, divisor):
                prime[multiple] = False
        divisor += 1
    values = [i for i in range(2, limit+1) if prime[i]]
    count = len(values)
    infinity = count+1
    suffix = [[infinity]*(s+1) for _ in range(count+1)]
    suffix[count][0] = 0
    for index in range(count-1, -1, -1):
        following = suffix[index+1]
        current = following.copy()
        value = values[index]
        for total in range(value, s+1):
            current[total] = min(current[total], following[total-value]+1)
        suffix[index] = current
    total = s
    while total > 0 and suffix[0][total] == infinity:
        total -= 1
    if total == 0:
        return []
    remaining = suffix[0][total]
    answer = []
    for index, value in enumerate(values):
        if total >= value and suffix[index+1][total-value]+1 == remaining:
            answer.append(value)
            total -= value
            remaining -= 1
        if total == 0:
            break
    return answer
