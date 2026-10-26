"""3767. Maximize Points After Choosing K Tasks."""
from __future__ import annotations


def solve(technique1: list[int], technique2: list[int], k: int) -> int:
    """O(n log n) time and O(n) auxiliary space; choose at least k, not necessarily exactly k, first-technique tasks."""
    differences = sorted((first - second for first, second in zip(technique1, technique2)), reverse=True)
    answer = sum(technique2)
    for index, difference in enumerate(differences):
        if index < k or difference > 0:
            answer += difference
    return answer


class Solution:
    def maxPoints(self, technique1: list[int], technique2: list[int], k: int) -> int:
        return solve(technique1, technique2, k)
