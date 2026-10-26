"""2262. Total Appeal of A String."""


def solve(s: str) -> int:
    """Last occurrence contributions for substrings ending at each position; O(n) time and O(26) space. Inputs are preserved."""
    last = [-1] * 26
    ending = 0
    answer = 0
    for index, character in enumerate(s):
        letter = ord(character) - ord('a')
        ending += index - last[letter]
        last[letter] = index
        answer += ending
    return answer


class Solution:
    def appealSum(self, s: str) -> int:
        return solve(s)
