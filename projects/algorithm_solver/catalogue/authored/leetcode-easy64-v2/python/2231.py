"""2231. Largest Number After Digit Swaps by Parity (Easy).

Specification: https://leetcode.com/problems/largest-number-after-digit-swaps-by-parity/description/
"""


def solve(num: int) -> int:
    """O(d log d) time, O(d) space; the declared integer domain is exact in Number."""
    digits = [int(character) for character in str(num)]
    even = sorted((digit for digit in digits if digit % 2 == 0), reverse=True)
    odd = sorted((digit for digit in digits if digit % 2 != 0), reverse=True)
    even_index = odd_index = 0
    result = 0
    for digit in digits:
        if digit % 2 == 0:
            replacement = even[even_index]
            even_index += 1
        else:
            replacement = odd[odd_index]
            odd_index += 1
        result = result * 10 + replacement
    return result


class Solution:
    def largestInteger(self, num: int) -> int:
        return solve(num)
