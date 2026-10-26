"""2486. Append Characters to String to Make Subsequence: greedily match the longest target prefix before appending its remaining suffix."""


def solve(s: str, t: str) -> int:
    """O(len(s)) time and O(1) auxiliary space; inputs are read-only."""
    matched = 0
    for character in s:
        if matched < len(t) and character == t[matched]:
            matched += 1
    return len(t) - matched


class Solution:
    def appendCharacters(self, s: str, t: str) -> int:
        return solve(s, t)
