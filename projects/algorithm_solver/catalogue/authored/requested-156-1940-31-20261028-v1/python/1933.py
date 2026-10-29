"""Original frontend 1933 variant; qualification unknown."""


def solve(s: str) -> bool:
    twos = 0
    i = 0
    n = len(s)
    while i < n:
        j = i
        while j < n and s[j] == s[i]:
            j += 1
        rem = (j - i) % 3
        if rem == 1:
            return False
        if rem == 2:
            twos += 1
        i = j
    return twos == 1


isDecomposable = solve


class Solution:
    def isDecomposable(self, s: str) -> bool:
        return solve(s)
