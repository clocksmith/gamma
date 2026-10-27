"""3628. Maximum Number of Subsequences After One Inserting.

Specification: https://leetcode.com/problems/maximum-number-of-subsequences-after-one-inserting/description/
Authored candidate; not executed, syntax-checked, tested, or Gamma-qualified.
O(n) time, O(1) space; count LCT subsequences and the best insertion of L, C, or T.
Inputs are not modified.
"""

def solve(s):
    left_count = left_center = original = 0
    center_right = right_count = 0
    for character in s:
        if character == 'L':
            left_count += 1
        elif character == 'C':
            left_center += left_count
        elif character == 'T':
            original += left_center
    for character in reversed(s):
        if character == 'T':
            right_count += 1
        elif character == 'C':
            center_right += right_count
    best_center = 0
    left = 0
    right = right_count
    for character in s:
        best_center = max(best_center, left * right)
        if character == 'L':
            left += 1
        elif character == 'T':
            right -= 1
    best_center = max(best_center, left * right)
    return original + max(left_center, center_right, best_center)


class Solution:
    def numOfSubsequences(self, s):
        return solve(s)
