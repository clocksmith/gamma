"""1616. Split Two Strings to Make Palindrome: match cross-string ends then test either remaining middle."""


def solve(a: str, b: str) -> bool:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    def palindrome(text: str, left: int, right: int) -> bool:
        while left < right:
            if text[left] != text[right]:
                return False
            left += 1
            right -= 1
        return True

    def compatible(first: str, second: str) -> bool:
        left, right = 0, len(first) - 1
        while left < right and first[left] == second[right]:
            left += 1
            right -= 1
        return palindrome(first, left, right) or palindrome(second, left, right)

    return compatible(a, b) or compatible(b, a)


class Solution:
    def checkPalindromeFormation(self, a: str, b: str) -> bool:
        return solve(a, b)
