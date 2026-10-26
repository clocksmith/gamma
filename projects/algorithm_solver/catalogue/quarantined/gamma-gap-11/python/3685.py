"""3685. Subsequence Sum After Capping Elements."""
from __future__ import annotations


def solve(nums: list[int], k: int) -> list[bool]:
    """O(n * k) time and O(n + k) auxiliary space; inputs are preserved."""
    n = len(nums)
    frequency = [0] * (n + 1)
    for value in nums:
        frequency[value] += 1
    reachable = [False] * (k + 1)
    reachable[0] = True
    remaining = n
    answer = []
    for cap in range(1, n + 1):
        possible = False
        for count in range(min(remaining, k // cap) + 1):
            if reachable[k - count * cap]:
                possible = True
                break
        answer.append(possible)
        for _ in range(frequency[cap]):
            for total in range(k, cap - 1, -1):
                reachable[total] = reachable[total] or reachable[total - cap]
        remaining -= frequency[cap]
    return answer


class Solution:
    def subsequenceSumAfterCapping(self, nums: list[int], k: int) -> list[bool]:
        return solve(nums, k)
