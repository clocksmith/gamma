# 524 — Longest Word in Dictionary through Deleting. Original implementation; authored candidate, not independently qualified.
def solve(s, dictionary):
    answer = ''
    for word in dictionary:
        if len(word) < len(answer) or len(word) == len(answer) and word >= answer:
            continue
        i = 0
        for char in s:
            if i < len(word) and word[i] == char:
                i += 1
        if i == len(word):
            answer = word
    return answer

findLongestWord = solve

class Solution:
    findLongestWord = staticmethod(solve)
