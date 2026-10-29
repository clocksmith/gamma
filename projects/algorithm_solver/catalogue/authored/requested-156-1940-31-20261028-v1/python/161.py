"""Original frontend 161 variant; qualification unknown."""


def solve(s: str, t: str) -> bool:
    if len(s) > len(t):
        s, t = t, s
    if len(t) - len(s) > 1:
        return False
    for i in range(len(s)):
        if s[i] != t[i]:
            if len(s) == len(t):
                return s[i + 1 :] == t[i + 1 :]
            return s[i:] == t[i + 1 :]
    return len(t) == len(s) + 1


isOneEditDistance = solve


class Solution:
    def isOneEditDistance(self, s: str, t: str) -> bool:
        return solve(s, t)
