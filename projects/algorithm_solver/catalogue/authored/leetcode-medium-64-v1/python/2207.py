"""2207. Maximize Number of Subsequences in a String: count existing pairs then choose the better endpoint insertion."""


def solve(text: str, pattern: str) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    first_count = second_count = answer = 0
    for character in text:
        # Count completed pairs before adding this position as a first character.
        if character == pattern[1]:
            answer += first_count
            second_count += 1
        if character == pattern[0]:
            first_count += 1
    return answer + max(first_count, second_count)


class Solution:
    def maximumSubsequenceCount(self, text: str, pattern: str) -> int:
        return solve(text, pattern)
