"""2002. Maximum Product of the Length of Two Palindromic Subsequences: combine a palindromic mask with the best palindromic submask of its complement."""


def solve(s: str) -> int:
    """O(n * 2^n) time and O(2^n) auxiliary space; inputs are read-only."""
    size = 1 << len(s)
    palindrome = [0] * size
    for mask in range(1, size):
        letters = [s[index] for index in range(len(s)) if mask & (1 << index)]
        if letters == letters[::-1]:
            palindrome[mask] = len(letters)
    best_subset = palindrome[:]
    for index in range(len(s)):
        bit = 1 << index
        for mask in range(size):
            if mask & bit:
                best_subset[mask] = max(best_subset[mask], best_subset[mask ^ bit])
    full = size - 1
    return max(palindrome[mask] * best_subset[full ^ mask] for mask in range(size))


class Solution:
    def maxProduct(self, s: str) -> int:
        return solve(s)
