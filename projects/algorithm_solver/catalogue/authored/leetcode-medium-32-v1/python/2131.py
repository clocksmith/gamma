"""2131. Longest Palindrome by Concatenating Two Letter Words: pair reversed words and reserve one symmetric center."""


def solve(words: list[str]) -> int:
    """O(n) expected time and O(1) auxiliary space for 26^2 possible words; inputs are read-only."""
    unmatched = {}
    length = 0
    for word in words:
        reverse = word[::-1]
        if unmatched.get(reverse, 0):
            unmatched[reverse] -= 1
            length += 4
        else:
            unmatched[word] = unmatched.get(word, 0) + 1
    for word, count in unmatched.items():
        if count and word[0] == word[1]:
            return length + 2
    return length


class Solution:
    def longestPalindrome(self, words: list[str]) -> int:
        return solve(words)
