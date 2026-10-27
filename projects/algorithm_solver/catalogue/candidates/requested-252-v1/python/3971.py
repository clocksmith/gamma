"""3971. Maximum Total Value.

Specification: https://leetcode.com/problems/maximum-total-value/description/
"""

from __future__ import annotations


def solve(value: list[int], decay: list[int], m: int) -> int:
    """O(n log V) time and O(1) auxiliary space; exact AP sums use BigInt in JavaScript. Inputs are preserved."""
    low, high = 0, max(value)
    def count_above(threshold):
        count = 0
        for initial, decrease in zip(value, decay):
            if initial > threshold:
                count += (initial - threshold - 1) // decrease + 1
            if count > m:
                break
        return count
    while low < high:
        middle = (low + high) // 2
        if count_above(middle) <= m:
            high = middle
        else:
            low = middle + 1
    selected = total = 0
    modulus = 1_000_000_007
    for initial, decrease in zip(value, decay):
        if initial <= low:
            continue
        count = (initial - low - 1) // decrease + 1
        selected += count
        total = (total + count * (2 * initial - (count - 1) * decrease) // 2) % modulus
    return (total + (m - selected) * low) % modulus
