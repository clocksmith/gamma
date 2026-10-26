"""2405. Optimal Partition of String: start a new partition exactly when the next letter repeats in the current one."""


def solve(s: str) -> int:
    """O(n) time and O(1) auxiliary space for lowercase English letters; inputs are read-only."""
    if not s:
        return 0
    mask = 0
    answer = 1
    for character in s:
        bit = 1 << (ord(character) - ord('a'))
        if mask & bit:
            answer += 1
            mask = 0
        mask |= bit
    return answer


class Solution:
    def partitionString(self, s: str) -> int:
        return solve(s)
