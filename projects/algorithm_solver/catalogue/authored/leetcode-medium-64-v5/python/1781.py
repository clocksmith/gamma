"""1781. Sum of Beauty of All Substrings: extend each starting position while tracking nonzero letter frequencies."""


def solve(s: str) -> int:
    """O(26 * n^2) time and O(26) auxiliary space; inputs are read-only."""
    result = 0
    for left in range(len(s)):
        counts = [0] * 26
        largest = 0
        for right in range(left, len(s)):
            letter = ord(s[right]) - ord('a')
            counts[letter] += 1
            largest = max(largest, counts[letter])
            smallest = min(count for count in counts if count > 0)
            result += largest - smallest
    return result


class Solution:
    def beautySum(self, s: str) -> int:
        return solve(s)
