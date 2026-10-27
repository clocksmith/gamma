"""3910. Count Connected Subgraphs with Even Node Sum
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/count-connected-subgraphs-with-even-node-sum/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3910.Count%20Connected%20Subgraphs%20with%20Even%20Node%20Sum/README_EN.md
Complexity: O(n*2^n + m) time, O(2^n+n) space.
n<=13, binary node values, undirected simple graph. Canonical solve; native method pending.
"""

from __future__ import annotations

def solve(nums, edges):
    n = len(nums)
    neighbors = [0] * n
    for first, second in edges:
        neighbors[first] |= 1 << second
        neighbors[second] |= 1 << first
    parity = [0] * (1 << n)
    answer = 0
    for subset in range(1, 1 << n):
        first = subset & -subset
        parity[subset] = parity[subset ^ first] ^ nums[first.bit_length() - 1]
        if parity[subset]:
            continue
        frontier = first
        reached = 0
        while frontier:
            bit = frontier & -frontier
            frontier ^= bit
            reached |= bit
            frontier |= neighbors[bit.bit_length() - 1] & subset & ~reached
        if reached == subset:
            answer += 1
    return answer
