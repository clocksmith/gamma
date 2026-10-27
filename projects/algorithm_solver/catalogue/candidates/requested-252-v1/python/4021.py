"""4021. Minimum Operations to Make a Rotated Palindrome I
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/minimum-operations-to-make-a-rotated-palindrome-i/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4021.Minimum%20Operations%20to%20Make%20a%20Rotated%20Palindrome%20I/README_EN.md
Complexity: O(n^2) time, O(n) space.
Each mirrored pair can be equalized by advancing one endpoint along the shorter alphabet arc. Increment operations commute with rotation; no rotation count >=n is needed.
"""

from __future__ import annotations

def solve(s):
    letters = [ord(ch) - 97 for ch in s]
    n = len(s)
    answer = 13 * (n // 2)
    for shift in range(n):
        if shift >= answer:
            break
        cost = shift
        for i in range(n // 2):
            difference = abs(letters[(shift + i) % n] - letters[(shift + n - 1 - i) % n])
            cost += min(difference, 26 - difference)
            if cost >= answer:
                break
        answer = min(answer, cost)
    return answer


class Solution:
    def minOperations(self, s):
        return solve(s)
