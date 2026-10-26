"""3871. Count Commas in Range II."""
from __future__ import annotations


def solve(n: int) -> int:
    """O(log_1000(n)) time and O(1) space; count one extra comma at each thousand-power threshold."""
    answer = 0
    threshold = 1000
    while threshold <= n:
        answer += n - threshold + 1
        if threshold > n // 1000:
            break
        threshold *= 1000
    return answer


class Solution:
    def countCommas(self, n: int) -> int:
        return solve(n)
