"""1423. Maximum Points You Can Obtain from Cards: exchange cards from the left prefix for the right suffix."""


def solve(cardPoints: list[int], k: int) -> int:
    """O(k) time and O(1) auxiliary space; inputs are read-only."""
    total = 0
    for index in range(k):
        total += cardPoints[index]
    best = total
    for taken_right in range(1, k + 1):
        total += cardPoints[-taken_right] - cardPoints[k - taken_right]
        best = max(best, total)
    return best


class Solution:
    def maxScore(self, cardPoints: list[int], k: int) -> int:
        return solve(cardPoints, k)
