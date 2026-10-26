"""3720. Lexicographically Smallest Permutation Greater Than Target."""
from __future__ import annotations


def solve(s: str, target: str) -> str:
    """O(26n) time and O(n) space; keep the longest feasible equal prefix, then take the smallest increase."""
    counts = [0] * 26
    for char in s:
        counts[ord(char) - 97] += 1
    prefix = []
    position = 0
    while position < len(target) and counts[ord(target[position]) - 97]:
        digit = ord(target[position]) - 97
        counts[digit] -= 1
        prefix.append(target[position])
        position += 1
    while True:
        if position < len(target):
            for digit in range(ord(target[position]) - 96, 26):
                if counts[digit]:
                    counts[digit] -= 1
                    suffix = ''.join(chr(97 + value) * counts[value] for value in range(26))
                    return ''.join(prefix) + chr(97 + digit) + suffix
        if not prefix:
            return ''
        position -= 1
        restored = prefix.pop()
        counts[ord(restored) - 97] += 1


class Solution:
    def lexGreaterPermutation(self, s: str, target: str) -> str:
        return solve(s, target)
