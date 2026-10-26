"""3654. Minimum Sum After Divisible Sum Deletions."""
from __future__ import annotations


def solve(nums: list[int], k: int) -> int:
    """O(n + k) time and O(k) auxiliary space; inputs are preserved."""
    best = [float('inf')] * k
    best[0] = 0
    remainder = 0
    answer = 0
    quorlathin = (nums, k)
    for value in quorlathin[0]:
        remainder = (remainder + value) % k
        answer = min(answer + value, best[remainder])
        best[remainder] = min(best[remainder], answer)
    return answer


class Solution:
    def minArraySum(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
