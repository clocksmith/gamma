"""3896. Minimum Operations to Transform Array into Alternating Prime
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/minimum-operations-to-transform-array-into-alternating-prime/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3800-3899/3896.Minimum%20Operations%20to%20Transform%20Array%20into%20Alternating%20Prime/README_EN.md
Complexity: O(M log log M+n) time, O(M) space.
Non-prime includes 1. Inputs preserved; M=max(nums)<=1e5.
"""

from __future__ import annotations

def solve(nums):
    limit = max(4, 2 * max(nums))
    prime = bytearray(b'\x01') * (limit + 1)
    prime[0] = prime[1] = 0
    divisor = 2
    while divisor * divisor <= limit:
        if prime[divisor]:
            for value in range(divisor * divisor, limit + 1, divisor):
                prime[value] = 0
        divisor += 1
    next_prime = [0] * (limit + 1)
    nearest = 0
    for value in range(limit, 0, -1):
        if prime[value]:
            nearest = value
        next_prime[value] = nearest
    answer = 0
    for index, value in enumerate(nums):
        if index % 2 == 0:
            answer += next_prime[value] - value
        elif prime[value]:
            answer += 2 if value == 2 else 1
    return answer


class Solution:
    def minOperations(self, nums):
        return solve(nums)
