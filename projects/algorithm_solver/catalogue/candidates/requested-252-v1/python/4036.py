"""4036. Lexicographically Largest String After Pair Transformations
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/lexicographically-largest-string-after-pair-transformations/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4036.Lexicographically%20Largest%20String%20After%20Pair%20Transformations/README_EN.md
Complexity: O(26n + output length) time, output-sized space.
Letter weight is 2^index. Only z may repeat after greedy decomposition; zz is not merged. Inputs preserved.
"""

from __future__ import annotations

def solve(nums):
    answer = []
    for value in nums:
        result = []
        for bit in range(25, -1, -1):
            count, value = divmod(value, 1 << bit)
            result.append(chr(97+bit) * count)
        answer.append(''.join(result))
    return answer


class Solution:
    def largestString(self, nums):
        return solve(nums)
