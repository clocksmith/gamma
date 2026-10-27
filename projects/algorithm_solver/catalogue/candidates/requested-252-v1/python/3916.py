"""3916. Number of ZigZag Arrays III.

Specification: https://leetcode.com/problems/number-of-zigzag-arrays-iii/description/
"""

from __future__ import annotations


def solve(n: int, l: int, r: int) -> int:
    """O(n^3+log MOD) time and O(n) space; exact modular interpolation, n <= 200. Inputs are preserved."""
    modulus = 1_000_000_007
    choices = r - l + 1
    samples = [0] * (n + 1)
    # The alternating strict-poset order polynomial has degree at most n.
    for size in range(1, n + 1):
        counts = [1] * size
        for length in range(2, n + 1):
            following = [0] * size
            running = 0
            indices = range(size) if length % 2 == 0 else range(size - 1, -1, -1)
            for value in indices:
                following[value] = running
                running = (running + counts[value]) % modulus
            counts = following
        samples[size] = 2 * sum(counts) % modulus
    if choices <= n:
        return samples[choices]
    factorial = [1] * (n + 1)
    for index in range(1, n + 1):
        factorial[index] = factorial[index - 1] * index % modulus
    inverse = [1] * (n + 1)
    inverse[n] = pow(factorial[n], modulus - 2, modulus)
    for index in range(n, 0, -1):
        inverse[index - 1] = inverse[index] * index % modulus
    prefix = [1] * (n + 2)
    suffix = [1] * (n + 2)
    for index in range(n + 1):
        prefix[index + 1] = prefix[index] * (choices - index) % modulus
    for index in range(n, -1, -1):
        suffix[index] = suffix[index + 1] * (choices - index) % modulus
    answer = 0
    for index in range(n + 1):
        term = samples[index] * prefix[index] * suffix[index + 1] % modulus
        term = term * inverse[index] * inverse[n - index] % modulus
        answer = (answer + (-term if (n - index) % 2 else term)) % modulus
    return answer
