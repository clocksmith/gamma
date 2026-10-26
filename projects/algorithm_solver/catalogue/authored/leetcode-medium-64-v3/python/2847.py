"""2847. Smallest Number With Given Digit Product: factor into large digits and place the selected digits in increasing order."""


def solve(n: int) -> str:
    """O(log(n + 1)) time and output space on the stated integer domain; inputs are read-only."""
    if n < 1:
        raise ValueError('n must be positive')
    if n == 1:
        return '1'
    remaining = n
    digits = []
    for digit in range(9, 1, -1):
        while remaining % digit == 0:
            digits.append(str(digit))
            remaining //= digit
    if remaining != 1:
        return '-1'
    return ''.join(reversed(digits))


class Solution:
    def smallestNumber(self, n: int) -> str:
        return solve(n)
