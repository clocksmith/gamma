"""4059. Lexicographically Largest Power Array
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/lexicographically-largest-power-array/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4059.Lexicographically%20Largest%20Power%20Array/README_EN.md
Complexity: O(15n) time, O(n) space.
Ordered blocks encode exactly the higher-bit optimal-prefix restrictions. Split only the first block containing a zero for the current bit; sorting later blocks by that bit would impose an unjustified restriction. Inputs preserved.
"""

from __future__ import annotations

def solve(nums):
    blocks = [list(nums)]
    answer = []
    for bit in range(14, -1, -1):
        prefix = 0
        for index, block in enumerate(blocks):
            ones, zeros = [], []
            for value in block:
                (ones if value & (1 << bit) else zeros).append(value)
            prefix += len(ones)
            if zeros:
                replacement = ([ones] if ones else []) + [zeros]
                blocks[index:index+1] = replacement
                break
        answer.append(prefix)
    return answer
