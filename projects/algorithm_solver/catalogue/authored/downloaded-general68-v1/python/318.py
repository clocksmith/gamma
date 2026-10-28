"""318. Maximum Product of Word Lengths (Medium).

Specification: https://leetcode.com/problems/maximum-product-of-word-lengths/description/
"""


def _mask_of(word):
    mask = 0
    for ch in word:
        mask |= 1 << (ord(ch) - 97)
    return mask


def solve(words: list[str]) -> int:
    masks = [_mask_of(w) for w in words]
    best = 0
    for i in range(len(words)):
        for j in range(i + 1, len(words)):
            if masks[i] & masks[j] == 0:
                best = max(best, len(words[i]) * len(words[j]))
    return best


class Solution:
    def maxProduct(self, words: list[str]) -> int:
        return solve(words)
