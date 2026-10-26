"""2484. Count Palindromic Subsequences. Count reversed digit-pair combinations on each side of the center."""


def solve(s: str) -> int:
    """O(100*n) time and O(100) space. Inputs are preserved."""
    modulus = 1_000_000_007
    left_single = [0] * 10
    right_single = [0] * 10
    left_pairs = [[0] * 10 for _ in range(10)]
    right_pairs = [[0] * 10 for _ in range(10)]
    for char in reversed(s):
        digit = ord(char) - 48
        for other in range(10):
            right_pairs[digit][other] += right_single[other]
        right_single[digit] += 1
    answer = 0
    for char in s:
        digit = ord(char) - 48
        right_single[digit] -= 1
        for other in range(10):
            right_pairs[digit][other] -= right_single[other]
        for first in range(10):
            for second in range(10):
                answer = (answer + left_pairs[first][second] * right_pairs[second][first]) % modulus
        for other in range(10):
            left_pairs[other][digit] += left_single[other]
        left_single[digit] += 1
    return answer


class Solution:
    def countPalindromes(self, s: str) -> int:
        return solve(s)
