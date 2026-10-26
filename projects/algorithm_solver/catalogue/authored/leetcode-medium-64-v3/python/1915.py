"""1915. Number of Wonderful Substrings: count equal parity masks and masks differing in one of ten bits."""


def solve(word: str) -> int:
    """O(10 * n) time and O(2^10) auxiliary space; inputs are read-only."""
    counts = [0] * 1024
    counts[0] = 1
    mask = answer = 0
    for char in word:
        mask ^= 1 << (ord(char) - ord('a'))
        answer += counts[mask]
        for bit in range(10):
            answer += counts[mask ^ (1 << bit)]
        counts[mask] += 1
    return answer


class Solution:
    def wonderfulSubstrings(self, word: str) -> int:
        return solve(word)
