"""2781. Length of the Longest Valid Substring."""

def solve(word: str, forbidden: list[str]) -> int:
    """O(n*L^2 + F) expected time with substring copies; L<=10, F=forbidden characters."""
    blocked = set(forbidden)
    longest = max(map(len, forbidden))
    left = 0
    answer = 0
    for right in range(len(word)):
        first = max(left, right - longest + 1)
        for start in range(right, first - 1, -1):
            if word[start:right + 1] in blocked:
                # The latest forbidden start imposes the strongest new left boundary.
                left = start + 1
                break
        answer = max(answer, right - left + 1)
    return answer


class Solution:
    def longestValidSubstring(self, word: str, forbidden: list[str]) -> int:
        return solve(word, forbidden)
