"""443. String Compression (Medium).

Specification: https://leetcode.com/problems/string-compression/description/
"""


def solve(chars: list[str]) -> list[str]:
    result = []
    i = 0
    while i < len(chars):
        ch = chars[i]
        count = 0
        while i < len(chars) and chars[i] == ch:
            i += 1
            count += 1
        result.append(ch)
        if count > 1:
            result.extend(str(count))
    return result


class Solution:
    def compress(self, chars: list[str]) -> list[str]:
        return solve(chars)
