"""3703. Remove K-Balanced Substrings."""
from __future__ import annotations


def solve(s: str, k: int) -> str:
    """O(n + k) time and O(n + k) space; stack-based exact-pattern removal restores prior match state."""
    pattern = '(' * k + ')' * k
    length = len(pattern)
    failure = [0] * length
    matched = 0
    for index in range(1, length):
        while matched and pattern[index] != pattern[matched]:
            matched = failure[matched - 1]
        if pattern[index] == pattern[matched]:
            matched += 1
        failure[index] = matched
    characters = []
    states = []
    matched = 0
    for char in s:
        while matched and char != pattern[matched]:
            matched = failure[matched - 1]
        if char == pattern[matched]:
            matched += 1
        characters.append(char)
        states.append(matched)
        if matched == length:
            del characters[-length:]
            del states[-length:]
            matched = states[-1] if states else 0
    return ''.join(characters)


class Solution:
    def removeSubstring(self, s: str, k: int) -> str:
        return solve(s, k)
