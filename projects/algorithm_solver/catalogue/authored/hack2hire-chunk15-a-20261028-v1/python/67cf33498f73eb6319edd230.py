"""Hack2Hire 67cf33498f73eb6319edd230 (Build Longest Palindrome) over an INFERRED spec; qualification unknown."""


def solve(words):
    count = {}
    for word in words:
        count[word] = count.get(word, 0) + 1
    pairs = 0
    center = 0
    for word, c in count.items():
        mirror = word[::-1]
        if word == mirror:
            pairs += c // 2
            if c % 2:
                center = 1
        elif word < mirror and mirror in count:
            pairs += min(c, count[mirror])
    return (2 * pairs + center) * len(words[0])


class Solution:
    def longestPalindrome(self, words):
        return solve(words)
