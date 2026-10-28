from collections import Counter


def solve(words, k):
    return sum(count >= 2 for count in Counter(word[:k] for word in words if len(word) >= k).values())


class Solution:
    def prefixConnected(self, words, k):
        return solve(words, k)
