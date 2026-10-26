"""3167. Better Compression of String: parse full decimal counts and combine them in alphabetic order."""


def solve(compressed: str) -> str:
    """O(n) time and O(26) auxiliary space excluding output; inputs are read-only."""
    counts = [0] * 26
    index = 0
    while index < len(compressed):
        letter = ord(compressed[index]) - ord('a')
        index += 1
        count = 0
        while index < len(compressed) and '0' <= compressed[index] <= '9':
            count = count * 10 + ord(compressed[index]) - ord('0')
            index += 1
        counts[letter] += count
    return ''.join(chr(ord('a') + letter) + str(count) for letter, count in enumerate(counts) if count)


class Solution:
    def betterCompression(self, compressed: str) -> str:
        return solve(compressed)
