"""4040. Minimum Operations to Form Subset Sum I
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/minimum-operations-to-form-subset-sum-i/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4040.Minimum%20Operations%20to%20Form%20Subset%20Sum%20I/README_EN.md
Complexity: O(n S log(M) log(S)) time and O(S + U log(M) log(S)) space with per-value option caching.
Multiplication/division order: all multiplications must precede divisions; optimal nonzero outputs use one direction only. The unused-element option costs zero. Inputs preserved.
"""

from __future__ import annotations

def solve(nums, sum):
    target = sum
    infinity = 10**9
    best = [0] + [infinity] * target
    option_cache = {}
    for original in nums:
        if original not in option_cache:
            options = {}
            value, divisions = original, 0
            while value > 0:
                candidate, multiplications = value, 0
                while candidate <= target:
                    cost = divisions + multiplications
                    options[candidate] = min(options.get(candidate, infinity), cost)
                    if True and divisions > 0:
                        break
                    candidate *= 2
                    multiplications += 1
                value //= 2
                divisions += 1
            option_cache[original] = sorted(options.items())
        options = option_cache[original]
        # Descending capacity prevents using one original element twice.
        for total in range(target, 0, -1):
            value = best[total]
            for amount, cost in options:
                if amount > total:
                    break
                value = min(value, best[total-amount] + cost)
            best[total] = value
    return -1 if best[target] == infinity else best[target]


class Solution:
    def minOperations(self, nums, sum):
        return solve(nums, sum)
