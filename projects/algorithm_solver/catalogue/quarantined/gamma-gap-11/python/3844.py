"""3844. Longest Almost-Palindromic Substring."""
from __future__ import annotations


def solve(s: str) -> int:
    """O(n^2) time and O(n) space; rolling palindrome and exactly-one-deletion interval states."""
    n = len(s)
    previous_palindrome = bytearray(n)
    previous_almost = bytearray(n)
    answer = 1
    for left in range(n - 1, -1, -1):
        palindrome = bytearray(n)
        almost = bytearray(n)
        palindrome[left] = almost[left] = 1
        for right in range(left + 1, n):
            match = s[left] == s[right]
            palindrome[right] = match and (right == left + 1 or previous_palindrome[right - 1])
            almost[right] = previous_palindrome[right] or palindrome[right - 1] or (match and (right == left + 1 or previous_almost[right - 1]))
            if almost[right]:
                answer = max(answer, right - left + 1)
        previous_palindrome, previous_almost = palindrome, almost
    return answer


class Solution:
    def almostPalindromic(self, s: str) -> int:
        return solve(s)
