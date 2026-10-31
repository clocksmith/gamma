"""Original frontend 3023 variant; qualification unknown."""


def solve(stream, pattern) -> int:
    m = len(pattern)
    pi = [0] * m
    j = 0
    for i in range(1, m):
        while j > 0 and pattern[i] != pattern[j]:
            j = pi[j - 1]
        if pattern[i] == pattern[j]:
            j += 1
        pi[i] = j
    is_list = isinstance(stream, list)
    limit = len(stream) if is_list else 10**7
    j = 0
    for idx in range(limit):
        b = stream[idx] if is_list else stream.next()
        while j > 0 and b != pattern[j]:
            j = pi[j - 1]
        if b == pattern[j]:
            j += 1
            if j == m:
                return idx - m + 1
    return -1


findPattern = solve


class Solution:
    def findPattern(self, stream, pattern) -> int:
        return solve(stream, pattern)
