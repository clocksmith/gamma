"""2825. Make String a Subsequence Using Cyclic Increments: greedily match each target character using an unchanged or once-incremented source character."""


def solve(str1: str, str2: str) -> bool:
    """O(n + m) time and O(1) auxiliary space; inputs are read-only."""
    matched = 0
    for character in str1:
        if matched == len(str2):
            break
        next_character = chr((ord(character) - ord('a') + 1) % 26 + ord('a'))
        if str2[matched] == character or str2[matched] == next_character:
            matched += 1
    return matched == len(str2)


class Solution:
    def canMakeSubsequence(self, str1: str, str2: str) -> bool:
        return solve(str1, str2)
