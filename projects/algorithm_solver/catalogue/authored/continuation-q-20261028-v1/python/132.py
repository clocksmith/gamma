"""Original frontend 132 source-defined native ABI; qualification unknown."""

def solve(s):
    cuts = [i - 1 for i in range(len(s) + 1)]
    for center in range(len(s)):
        for left, right in ((center, center), (center, center + 1)):
            while left >= 0 and right < len(s) and s[left] == s[right]:
                cuts[right + 1] = min(cuts[right + 1], cuts[left] + 1)
                left -= 1
                right += 1
    return cuts[-1]


class Solution:
    def minCut(self, s):
        return solve(s)
