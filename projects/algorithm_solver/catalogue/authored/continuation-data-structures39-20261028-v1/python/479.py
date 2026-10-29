"""Original frontend 479 variant; qualification unknown."""


def solve(n: int) -> int:
    if n == 1:
        return 9
    upper = 10**n - 1
    lower = 10**(n - 1)
    for left in range(upper, lower - 1, -1):
        s = str(left)
        pal = int(s + s[::-1])
        d = upper
        while d * d >= pal:
            if pal % d == 0 and lower <= pal // d <= upper:
                return pal % 1337
            d -= 1
    return 9


largestPalindrome = solve


class Solution:
    def largestPalindrome(self, n: int) -> int:
        return solve(n)
