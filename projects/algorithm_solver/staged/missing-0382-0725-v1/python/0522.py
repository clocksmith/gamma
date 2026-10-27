"""522. Longest Uncommon Subsequence II."""

def solve(strs: list[str]) -> int:
    def subsequence(a, b):
        index = 0
        for char in b:
            if index < len(a) and a[index] == char:
                index += 1
        return index == len(a)
    order = sorted(range(len(strs)), key=lambda i: -len(strs[i]))
    for i in order:
        if all(i == j or not subsequence(strs[i], strs[j]) for j in range(len(strs))):
            return len(strs[i])
    return -1


class Solution:
    def findLUSlength(self, strs: list[str]) -> int:
        return solve(strs)
