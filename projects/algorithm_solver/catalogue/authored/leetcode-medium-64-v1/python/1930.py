"""1930. Unique Length-3 Palindromic Subsequences: count distinct middle letters between each outer letter first and last occurrence."""


def solve(s: str) -> int:
    """O(26 * n) time and O(1) auxiliary space for lowercase English letters; inputs are read-only."""
    first = [-1] * 26
    last = [-1] * 26
    for index, character in enumerate(s):
        letter = ord(character) - ord('a')
        if first[letter] == -1:
            first[letter] = index
        last[letter] = index
    answer = 0
    for letter in range(26):
        if last[letter] - first[letter] < 2:
            continue
        middle_mask = 0
        for index in range(first[letter] + 1, last[letter]):
            middle_mask |= 1 << (ord(s[index]) - ord('a'))
        answer += middle_mask.bit_count()
    return answer


class Solution:
    def countPalindromicSubsequence(self, s: str) -> int:
        return solve(s)
