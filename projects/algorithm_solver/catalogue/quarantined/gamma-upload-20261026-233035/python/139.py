"""139. Word Break."""
def solve(s: str, wordDict: list[str]) -> bool:
    words = set(wordDict)
    reachable = [False] * (len(s) + 1)
    reachable[0] = True
    maximum = max(map(len, words), default=0)
    for end in range(1, len(s) + 1):
        for length in range(1, min(maximum, end) + 1):
            if reachable[end - length] and s[end - length:end] in words:
                reachable[end] = True
                break
    return reachable[-1]

class Solution:
    def wordBreak(self, s: str, wordDict: list[str]) -> bool:
        return solve(s, wordDict)
