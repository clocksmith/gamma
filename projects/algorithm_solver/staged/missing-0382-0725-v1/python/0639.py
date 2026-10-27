"""639. Decode Ways II."""

def solve(s: str) -> int:
    modulus = 1_000_000_007
    def single(char):
        return 9 if char == '*' else int(char != '0')
    def pair(a, b):
        if a == '*' and b == '*':
            return 15
        if a == '*':
            return 2 if b <= '6' else 1
        if b == '*':
            return 9 if a == '1' else 6 if a == '2' else 0
        return int(10 <= int(a + b) <= 26)
    if not s:
        return 0
    previous, current = 1, single(s[0])
    for i in range(1, len(s)):
        previous, current = current, (current * single(s[i]) + previous * pair(s[i - 1], s[i])) % modulus
    return current


class Solution:
    def numDecodings(self, s: str) -> int:
        return solve(s)
