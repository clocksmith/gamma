"""2897. Apply Operations on Array to Maximize Sum of Squares.

Concentrate available bits into the k largest constructible values; O(30*(n+k)) time, O(30) space. Inputs are preserved.
"""

def solve(nums: list[int], k: int) -> int:
    counts = [sum(value >> bit & 1 for value in nums) for bit in range(30)]
    answer = 0
    for _ in range(k):
        value = 0
        for bit in range(30):
            if counts[bit]:
                counts[bit] -= 1
                value |= 1 << bit
        answer = (answer + value * value) % 1_000_000_007
    return answer


class Solution:
    def maxSum(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
