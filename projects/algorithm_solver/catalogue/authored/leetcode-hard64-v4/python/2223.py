"""2223. Sum of Scores of Built Strings."""


def solve(s: str) -> int:
    """Z-function prefix matches for every suffix; O(n) time and O(n) space. Inputs are preserved."""
    size = len(s)
    matches = [0] * size
    left = right = 0
    answer = size
    for index in range(1, size):
        if index < right:
            matches[index] = min(right - index, matches[index - left])
        while index + matches[index] < size and s[matches[index]] == s[index + matches[index]]:
            matches[index] += 1
        if index + matches[index] > right:
            left, right = index, index + matches[index]
        answer += matches[index]
    return answer


class Solution:
    def sumScores(self, s: str) -> int:
        return solve(s)
