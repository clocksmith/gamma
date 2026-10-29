"""Original LeetCode 639 candidate; qualification unknown."""

def solve(s):
    def single(c): return 9 if c == '*' else int(c != '0')
    def pair(a, b):
        if a == '*' and b == '*': return 15
        if a == '*': return 2 if b <= '6' else 1
        if b == '*': return 9 if a == '1' else 6 if a == '2' else 0
        return int(10 <= int(a + b) <= 26)
    previous, current = 1, single(s[0])
    for i in range(1, len(s)):
        previous, current = current, (single(s[i]) * current + pair(s[i-1], s[i]) * previous) % 1000000007
    return current


class Solution:
    def numDecodings(self, s):
        return solve(s)
