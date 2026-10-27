"""4028. Minimum Operations to Make a Rotated Palindrome II
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/minimum-operations-to-make-a-rotated-palindrome-ii/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4028.Minimum%20Operations%20to%20Make%20a%20Rotated%20Palindrome%20II/README_EN.md
Complexity: 13 exact big-integer squares on O(n log n) bits plus O(n log n) packing work; O(n log n) bits of storage.
Circular alphabet distance equals Hamming distance across 13 half-circle cuts. For each cut, mirrored disagreement cost is count(ones)-circular_self_convolution(axis). Carry-free Kronecker packing uses a coefficient base >13n and computes all costs exactly, without FFT rounding or optional dependencies. Runtime depends on built-in big-integer multiplication and is unmeasured.
"""

from __future__ import annotations

def solve(s):
    letters = [ord(ch) - 97 for ch in s]
    n = len(letters)
    width = ((13 * n).bit_length() + 7) // 8
    convolution = 0
    ones = 0
    for cut in range(13):
        packed = bytearray(n * width)
        for i, value in enumerate(letters):
            if (value - cut) % 26 < 13:
                packed[i * width] = 1
                ones += 1
        word = int.from_bytes(packed, 'little')
        convolution += word * word
    raw = convolution.to_bytes(2 * n * width, 'little')
    coefficients = [int.from_bytes(raw[i * width:(i + 1) * width], 'little') for i in range(2 * n)]
    return min(shift + ones - coefficients[(2 * shift + n - 1) % n] - coefficients[(2 * shift + n - 1) % n + n] for shift in range(n))


class Solution:
    def minOperations(self, s):
        return solve(s)
