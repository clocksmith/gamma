"""3261. Count Substrings That Satisfy K-Constraint II: first-invalid boundaries and prefix sums of valid suffix counts."""


def solve(s: str, k: int, queries: list[list[int]]) -> list[int]:
    """O(n + q) time and O(n + q) space. Inputs are preserved."""
    n = len(s)
    first_invalid = [n] * n
    prefix = [0] * (n + 1)
    counts = [0, 0]
    left = 0
    for right, character in enumerate(s):
        counts[ord(character) - ord('0')] += 1
        while counts[0] > k and counts[1] > k:
            first_invalid[left] = right
            counts[ord(s[left]) - ord('0')] -= 1
            left += 1
        prefix[right + 1] = prefix[right] + right - left + 1
    answer = []
    for left, right in queries:
        split = min(right + 1, first_invalid[left])
        width = split - left
        answer.append(width * (width + 1) // 2 + prefix[right + 1] - prefix[split])
    return answer


class Solution:
    def countKConstraintSubstrings(self, s: str, k: int, queries: list[list[int]]) -> list[int]:
        return solve(s, k, queries)
