"""3855. Sum of K-Digit Numbers in a Range."""
from __future__ import annotations


def solve(l: int, r: int, k: int) -> int:
    """O(log k) modular steps and O(1) auxiliary space; exact modular multiplication, including leading zeros."""
    modulus = 1_000_000_007
    choices = r - l + 1
    digit_sum = (l + r) * choices // 2
    repunit = (pow(10, k, modulus) - 1) * pow(9, modulus - 2, modulus) % modulus
    return digit_sum * pow(choices, k - 1, modulus) * repunit % modulus


class Solution:
    def sumOfNumbers(self, l: int, r: int, k: int) -> int:
        return solve(l, r, k)
