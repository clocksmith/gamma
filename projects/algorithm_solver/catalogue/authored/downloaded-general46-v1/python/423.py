"""423. Reconstruct Original Digits from English (Medium).

Specification: https://leetcode.com/problems/reconstruct-original-digits-from-english/description/
"""


def solve(s: str) -> str:
    counts = {}
    for ch in s:
        counts[ch] = counts.get(ch, 0) + 1
    digits = [0] * 10
    digits[0] = counts.get('z', 0)
    digits[2] = counts.get('w', 0)
    digits[4] = counts.get('u', 0)
    digits[6] = counts.get('x', 0)
    digits[8] = counts.get('g', 0)
    digits[3] = counts.get('h', 0) - digits[8]
    digits[5] = counts.get('f', 0) - digits[4]
    digits[7] = counts.get('s', 0) - digits[6]
    digits[1] = counts.get('o', 0) - digits[0] - digits[2] - digits[4]
    digits[9] = counts.get('i', 0) - digits[5] - digits[6] - digits[8]
    result = ''
    for d in range(10):
        result += str(d) * digits[d]
    return result


class Solution:
    def originalDigits(self, s: str) -> str:
        return solve(s)
