"""2165. Smallest Value of the Rearranged Number: sort negative magnitudes downward and place the first nonzero positive digit first."""


def solve(num: int) -> int:
    """O(d log d) time and O(d) auxiliary space for d decimal digits; inputs are read-only."""
    if num == 0:
        return 0
    digits = sorted(str(abs(num)), reverse=num < 0)
    if num < 0:
        return -int(''.join(digits))
    first = 0
    while digits[first] == '0':
        first += 1
    digits[0], digits[first] = digits[first], digits[0]
    return int(''.join(digits))


class Solution:
    def smallestNumber(self, num: int) -> int:
        return solve(num)
