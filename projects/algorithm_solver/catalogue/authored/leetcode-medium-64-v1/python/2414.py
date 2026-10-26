"""2414. Length of the Longest Alphabetical Continuous Substring: extend a run only when the next letter advances by one."""


def solve(s: str) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    current = answer = 0
    for index, character in enumerate(s):
        if index > 0 and ord(character) == ord(s[index - 1]) + 1:
            current += 1
        else:
            current = 1
        answer = max(answer, current)
    return answer


class Solution:
    def longestContinuousSubstring(self, s: str) -> int:
        return solve(s)
