"""Original frontend 3302 variant; qualification unknown."""


def solve(word1: str, word2: str):
    n, m = len(word1), len(word2)
    last = [-1] * (m + 1)
    last[m] = n
    j = m - 1
    for i in range(n - 1, -1, -1):
        if j >= 0 and word1[i] == word2[j]:
            last[j] = i
            j -= 1
    res = []
    j = 0
    used = False
    for i in range(n):
        if j == m:
            break
        if word1[i] == word2[j]:
            res.append(i)
            j += 1
        elif not used and last[j + 1] > i:
            used = True
            res.append(i)
            j += 1
    return res if len(res) == m else []


validSequence = solve


class Solution:
    def validSequence(self, word1: str, word2: str):
        return solve(word1, word2)
