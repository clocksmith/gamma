"""1946. Largest Number After Mutating Substring: start at the first strict improvement and stop before the first decrease."""


def solve(num: str, change: list[int]) -> str:
    """O(n) time and O(n) space; inputs are read-only."""
    digits = list(num)
    index = 0
    while index < len(digits) and change[ord(digits[index]) - ord('0')] <= ord(digits[index]) - ord('0'):
        index += 1
    while index < len(digits):
        digit = ord(digits[index]) - ord('0')
        if change[digit] < digit:
            break
        digits[index] = str(change[digit])
        index += 1
    return ''.join(digits)


class Solution:
    def maximumNumber(self, num: str, change: list[int]) -> str:
        return solve(num, change)
