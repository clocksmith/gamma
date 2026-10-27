"""140. Word Break II."""
from functools import lru_cache

def solve(s: str, wordDict: list[str]) -> list[str]:
    words = set(wordDict)
    maximum = max(map(len, words), default=0)
    @lru_cache(None)
    def build(start: int):
        if start == len(s):
            return ('',)
        result = []
        for end in range(start + 1, min(len(s), start + maximum) + 1):
            word = s[start:end]
            if word in words:
                for suffix in build(end):
                    result.append(word if not suffix else word + ' ' + suffix)
        return tuple(result)
    return list(build(0))

class Solution:
    def wordBreak(self, s: str, wordDict: list[str]) -> list[str]:
        return solve(s, wordDict)
