"""819. Most Common Word (Easy).

Specification: https://leetcode.com/problems/most-common-word/description/
"""


import re


def solve(paragraph: str, banned: list[str]) -> str:
    banned_set = set(banned)
    counts = {}
    best = ''
    best_count = 0
    for word in re.split(r'[^a-z]+', paragraph.lower()):
        if not word or word in banned_set:
            continue
        counts[word] = counts.get(word, 0) + 1
        if counts[word] > best_count:
            best_count = counts[word]
            best = word
    return best


class Solution:
    def mostCommonWord(self, paragraph: str, banned: list[str]) -> str:
        return solve(paragraph, banned)
