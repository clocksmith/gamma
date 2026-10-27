"""479. Largest Palindrome Product. Enumerate even-length palindromes in descending order with exact integer factor checks."""

def solve(n: int) -> int:
    if n == 1:
        return 9
    upper = 10 ** n - 1
    lower = 10 ** (n - 1)
    maximum = upper * upper
    for half in range(upper, lower - 1, -1):
        palindrome = int(str(half) + str(half)[::-1])
        if palindrome > maximum:
            continue
        # Every even-length decimal palindrome has a factor divisible by 11.
        minimum_factor = max(lower, (palindrome + upper - 1) // upper)
        factor = upper - upper % 11
        while factor >= minimum_factor:
            if palindrome % factor == 0:
                other = palindrome // factor
                if lower <= other <= upper:
                    return palindrome % 1337
            factor -= 11
    return 0


class Solution:
    def largestPalindrome(self, n: int) -> int:
        return solve(n)
