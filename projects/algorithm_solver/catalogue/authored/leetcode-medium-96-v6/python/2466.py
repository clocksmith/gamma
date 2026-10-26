"""2466. Count Ways To Build Good Strings: count strings by their final appended block and sum the permitted lengths."""


def solve(low: int, high: int, zero: int, one: int) -> int:
    """O(high) time and O(high) auxiliary space; inputs are read-only."""
    modulus = 1_000_000_007
    ways = [0] * (high + 1)
    ways[0] = 1
    answer = 0
    for length in range(1, high + 1):
        if length >= zero:
            ways[length] += ways[length - zero]
        if length >= one:
            ways[length] += ways[length - one]
        ways[length] %= modulus
        if length >= low:
            answer = (answer + ways[length]) % modulus
    return answer


class Solution:
    def countGoodStrings(self, low: int, high: int, zero: int, one: int) -> int:
        return solve(low, high, zero, one)
