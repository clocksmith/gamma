"""5. Longest Palindromic Substring."""
def solve(s: str) -> str:
    start = end = 0
    for center in range(len(s)):
        for left, right in ((center, center), (center, center + 1)):
            while left >= 0 and right < len(s) and s[left] == s[right]:
                left -= 1
                right += 1
            if right - left - 1 > end - start + 1:
                start, end = left + 1, right - 1
    return s[start:end + 1]

class Solution:
    def longestPalindrome(self, s: str) -> str:
        return solve(s)
