"""3639. Minimum Time to Activate String.

Specification: https://leetcode.com/problems/minimum-time-to-activate-string/description/
Authored candidate; not executed, syntax-checked, tested, or Gamma-qualified.
O(n log n) time, O(n) space; valid substrings contain at least one activated position.
Inputs are not modified.
"""

def solve(s, order, k):
    size = len(s)
    if k > size * (size + 1) // 2:
        return -1
    activation = [0] * size
    for time, index in enumerate(order):
        activation[index] = time
    def enough(time):
        invalid = run = 0
        for index in range(size):
            if activation[index] > time:
                run += 1
                invalid += run
            else:
                run = 0
        return size * (size + 1) // 2 - invalid >= k
    left, right = 0, size - 1
    while left < right:
        middle = (left + right) // 2
        if enough(middle):
            right = middle
        else:
            left = middle + 1
    return left


class Solution:
    def minTime(self, s, order, k):
        return solve(s, order, k)
