"""3035. Maximum Palindromes After Operations: spend globally available equal-character pairs on the shortest words first."""


def solve(words: list[str]) -> int:
    """O(S + n log n) time and O(n) auxiliary space, where S is the total character count; inputs are read-only."""
    counts = [0] * 26
    for word in words:
        for character in word:
            counts[ord(character) - ord('a')] += 1
    pairs = sum(count // 2 for count in counts)
    completed = 0
    for length in sorted(map(len, words)):
        needed = length // 2
        if needed > pairs:
            break
        pairs -= needed
        completed += 1
    return completed


class Solution:
    def maxPalindromesAfterOperations(self, words: list[str]) -> int:
        return solve(words)
