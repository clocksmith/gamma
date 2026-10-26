"""2472. Maximum Number of Non-overlapping Palindrome Substrings. Earliest-finish greedy over palindromes of length k or k+1."""


def solve(s: str, k: int) -> int:
    """O(n*k) time and O(1) space. Inputs are preserved."""
    def palindrome(left, right):
        while left < right:
            if s[left] != s[right]:
                return False
            left += 1
            right -= 1
        return True

    answer = 0
    available = 0
    for right in range(k - 1, len(s)):
        # Every longer palindrome contains an inner palindrome of one of these lengths.
        for length in (k, k + 1):
            left = right - length + 1
            if left >= available and palindrome(left, right):
                answer += 1
                available = right + 1
                break
    return answer


class Solution:
    def maxPalindromes(self, s: str, k: int) -> int:
        return solve(s, k)
