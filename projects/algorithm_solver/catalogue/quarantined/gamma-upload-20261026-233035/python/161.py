"""161. One Edit Distance."""
def solve(s: str, t: str) -> bool:
    if len(s) > len(t):
        s, t = t, s
    if len(t) - len(s) > 1:
        return False
    for index in range(len(s)):
        if s[index] != t[index]:
            return s[index + 1:] == t[index + 1:] if len(s) == len(t) else s[index:] == t[index + 1:]
    return len(t) == len(s) + 1

class Solution:
    def isOneEditDistance(self, s: str, t: str) -> bool:
        return solve(s, t)
