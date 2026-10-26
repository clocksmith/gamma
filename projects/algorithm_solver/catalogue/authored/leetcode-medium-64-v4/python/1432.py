"""1432. Max Difference You Can Get From Changing an Integer: replace the first improvable digit globally while keeping the minimum positive."""


def solve(num: int) -> int:
    """O(d) time and O(d) auxiliary space, where d is the number of digits; inputs are read-only."""
    digits = str(num)
    maximum = digits
    for digit in digits:
        if digit != '9':
            maximum = digits.replace(digit, '9')
            break
    minimum = digits
    if digits[0] != '1':
        minimum = digits.replace(digits[0], '1')
    else:
        for digit in digits[1:]:
            if digit not in '01':
                minimum = digits.replace(digit, '0')
                break
    return int(maximum) - int(minimum)


class Solution:
    def maxDiff(self, num: int) -> int:
        return solve(num)
