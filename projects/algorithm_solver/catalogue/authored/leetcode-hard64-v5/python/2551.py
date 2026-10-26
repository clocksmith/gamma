"""2551. Put Marbles in Bags. Compare the largest and smallest adjacent-pair boundary sums."""


def solve(weights: list[int], k: int) -> int:
    """O(n log n) time and O(n) space. Inputs are preserved."""
    boundaries = sorted(weights[index] + weights[index + 1] for index in range(len(weights) - 1))
    answer = 0
    for index in range(k - 1):
        answer += boundaries[-1 - index] - boundaries[index]
    return answer


class Solution:
    def putMarbles(self, weights: list[int], k: int) -> int:
        return solve(weights, k)
