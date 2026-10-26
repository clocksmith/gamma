"""1771. Maximize Palindrome Length From Subsequences."""


def solve(word1: str, word2: str) -> int:
    """Interval DP with a crossing endpoint pair; O(L^2) time and O(L) space. Inputs are preserved."""
    text = word1 + word2
    size = len(text)
    boundary = len(word1)
    best = [0] * size
    answer = 0
    for left in range(size - 1, -1, -1):
        diagonal = 0
        best[left] = 1
        for right in range(left + 1, size):
            previous = best[right]
            if text[left] == text[right]:
                best[right] = diagonal + 2
                if left < boundary <= right:
                    answer = max(answer, best[right])
            else:
                best[right] = max(best[right], best[right - 1])
            diagonal = previous
    return answer


class Solution:
    def longestPalindrome(self, word1: str, word2: str) -> int:
        return solve(word1, word2)
