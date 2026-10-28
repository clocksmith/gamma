"""1720. Decode XORed Array (Easy).

Specification: https://leetcode.com/problems/decode-xored-array/description/
"""


def solve(encoded: list[int], first: int) -> list[int]:
    result = [first]
    for value in encoded:
        result.append(result[-1] ^ value)
    return result


class Solution:
    def decode(self, encoded: list[int], first: int) -> list[int]:
        return solve(encoded, first)
