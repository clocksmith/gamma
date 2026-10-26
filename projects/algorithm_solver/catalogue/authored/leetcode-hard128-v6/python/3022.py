"""3022. Minimize OR of Remaining Elements Using Operations.

Greedily forbid bits and count zero-AND segments for each candidate mask; O(30*n) time, O(1) space. Inputs are preserved.
"""

def solve(nums: list[int], k: int) -> int:
    forbidden = answer = 0
    for bit in range(29, -1, -1):
        candidate = forbidden | 1 << bit
        current = (1 << 30) - 1
        segments = 0
        for value in nums:
            current &= value
            if current & candidate == 0:
                segments += 1
                current = (1 << 30) - 1
        if len(nums) - segments <= k:
            forbidden = candidate
        else:
            answer |= 1 << bit
    return answer


class Solution:
    def minOrAfterOperations(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
