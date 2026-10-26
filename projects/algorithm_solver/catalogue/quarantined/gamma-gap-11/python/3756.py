"""3756. Concatenate Non-Zero Digits and Multiply by Sum II."""
from __future__ import annotations


def solve(s: str, queries: list[list[int]]) -> list[int]:
    """O(n + q) time and O(n) auxiliary space; modular multiplication uses exact split products in JavaScript."""
    modulus = 1_000_000_007
    prefix = [0]
    sums = [0]
    counts = [0]
    powers = [1]
    for char in s:
        digit = int(char)
        prefix.append((prefix[-1] * 10 + digit) % modulus if digit else prefix[-1])
        sums.append(sums[-1] + digit)
        counts.append(counts[-1] + int(digit != 0))
        powers.append(powers[-1] * 10 % modulus)
    answer = []
    for left, right in queries:
        length = counts[right + 1] - counts[left]
        value = (prefix[right + 1] - prefix[left] * powers[length]) % modulus
        answer.append(value * (sums[right + 1] - sums[left]) % modulus)
    return answer


class Solution:
    def sumAndMultiply(self, s: str, queries: list[list[int]]) -> list[int]:
        return solve(s, queries)
