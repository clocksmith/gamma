"""2377. Check if Number Has Equal Digit Count and Digit Value (Easy).

Specification: https://leetcode.com/problems/check-if-number-has-equal-digit-count-and-digit-value/description/
"""


def solve(num):
    for i in range(len(num)):
        if num.count(str(i)) != int(num[i]):
            return False
    return True


class Solution:
    def digitCount(self, num):
        return solve(num)
