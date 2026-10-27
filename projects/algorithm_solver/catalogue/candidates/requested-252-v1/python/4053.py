"""4053. Minimum Operations to Make Every Element Palindromic
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/minimum-operations-to-make-every-element-palindromic/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4053.Minimum%20Operations%20to%20Make%20Every%20Element%20Palindromic/README_EN.md
Complexity: O(P log P + n log P) time, O(P) space, P=200000 generated palindromes.
Targets are positive and must preserve input parity because each operation changes a value by two. Precomputation occurs only inside solve; inputs preserved.
"""

from __future__ import annotations
from bisect import bisect_left

def solve(nums):
    palindromes = [[], []]
    # Covers all <=9-digit palindromes and a same-parity upper neighbor above 10^9.
    for prefix in range(1, 100001):
        s = str(prefix)
        for text in (s+s[::-1], s+s[:-1][::-1]):
            value = int(text)
            palindromes[value % 2].append(value)
    for values in palindromes:
        values.sort()
    answer = 0
    for value in nums:
        values = palindromes[value % 2]
        p = bisect_left(values, value)
        difference = values[p]-value if p < len(values) else float('inf')
        if p:
            difference = min(difference, value-values[p-1])
        answer += difference//2
    return answer


class Solution:
    def minOperations(self, nums):
        return solve(nums)
