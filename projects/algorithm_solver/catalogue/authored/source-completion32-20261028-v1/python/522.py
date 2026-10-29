# 522 — Longest Uncommon Subsequence II. Original implementation; authored candidate, not independently qualified.
def solve(strs):
    def subsequence(a, b):
        i = 0
        for char in b:
            if i < len(a) and a[i] == char:
                i += 1
        return i == len(a)
    answer = -1
    for i, word in enumerate(strs):
        if len(word) > answer and all(i == j or not subsequence(word, other) for j, other in enumerate(strs)):
            answer = len(word)
    return answer

findLUSlength = solve

class Solution:
    findLUSlength = staticmethod(solve)
