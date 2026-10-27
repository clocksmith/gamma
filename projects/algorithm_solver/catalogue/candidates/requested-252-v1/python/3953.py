"""3953. Maximum Score with Co-Prime Element
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/maximum-score-with-co-prime-element/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3953.Maximum%20Score%20with%20Co-Prime%20Element/README_EN.md
Complexity: O(M log M + M*2^omega(M)) time, O(M) space for M <= 100000.
Unchanged original values above maxVal remain selectable. Modification limits apply only to replacement values. Coprimality count includes the selected index and explicitly removes its contribution. Inputs preserved; native method pending.
"""

from __future__ import annotations

def solve(nums, maxVal):
    bound = max(maxVal, max(nums))
    frequency = [0] * (bound + 1)
    for value in nums:
        frequency[value] += 1
    multiples = [0] * (bound + 1)
    smallest_prime = [0] * (bound + 1)
    for divisor in range(1, bound + 1):
        multiples[divisor] = sum(frequency[divisor::divisor])
        if divisor >= 2 and smallest_prime[divisor] == 0:
            for multiple in range(divisor, bound + 1, divisor):
                if smallest_prime[multiple] == 0:
                    smallest_prime[multiple] = divisor
    best = 0
    for value in range(bound, 0, -1):
        if value <= best:
            break
        if value > maxVal and frequency[value] == 0:
            continue
        if value == 1:
            cost = 0 if frequency[1] else 1
        else:
            terms = [(1, -1)]
            remainder = value
            while remainder > 1:
                prime = smallest_prime[remainder]
                terms += [(product * prime, -sign) for product, sign in terms]
                while remainder % prime == 0:
                    remainder //= prime
            bad = sum(sign * multiples[product] for product, sign in terms[1:])
            cost = bad - 1 if frequency[value] else max(1, bad)
        best = max(best, value - cost)
    return best
