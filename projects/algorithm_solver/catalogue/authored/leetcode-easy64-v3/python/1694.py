"""1694. Reformat Phone Number (Easy).

Specification: https://leetcode.com/problems/reformat-phone-number/description/
"""


def solve(number: str) -> str:
    """O(n) time and space; format the final four digits as two pairs."""
    digits = number.replace(' ', '').replace('-', '')
    groups = []
    index = 0
    while len(digits) - index > 4:
        groups.append(digits[index:index + 3])
        index += 3
    if len(digits) - index == 4:
        groups.append(digits[index:index + 2])
        groups.append(digits[index + 2:])
    else:
        groups.append(digits[index:])
    return '-'.join(groups)


class Solution:
    def reformatNumber(self, number: str) -> str:
        return solve(number)
