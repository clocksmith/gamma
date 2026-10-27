"""438. Find All Anagrams in a String."""

from collections import Counter

def solve(s: str, p: str) -> list[int]:
    needed = Counter(p)
    missing = len(p)
    answer = []
    for right, char in enumerate(s):
        if needed[char] > 0:
            missing -= 1
        needed[char] -= 1
        if right >= len(p):
            outgoing = s[right - len(p)]
            needed[outgoing] += 1
            if needed[outgoing] > 0:
                missing += 1
        if right + 1 >= len(p) and missing == 0:
            answer.append(right - len(p) + 1)
    return answer


class Solution:
    def findAnagrams(self, s: str, p: str) -> list[int]:
        return solve(s, p)
