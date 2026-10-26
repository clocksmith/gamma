"""2014. Longest Subsequence Repeated k Times.

Breadth-first extension of repeatable candidates, bounded by per-letter quotas. O(n*A*C) time, O(C*L) space for C candidates of length at most L.
"""

from collections import Counter


def solve(s: str, k: int) -> str:
    counts = Counter(s)
    alphabet = sorted(char for char in counts if counts[char] >= k)

    def repeats(candidate):
        position = complete = 0
        for char in s:
            if char == candidate[position]:
                position += 1
                if position == len(candidate):
                    complete += 1
                    if complete == k:
                        return True
                    position = 0
        return False

    level = ['']
    answer = ''
    while level:
        following = []
        for prefix in level:
            for char in alphabet:
                if prefix.count(char) >= counts[char] // k:
                    continue
                candidate = prefix + char
                if repeats(candidate):
                    following.append(candidate)
                    answer = candidate
        level = following
    return answer


class Solution:
    def longestSubsequenceRepeatedK(self, s: str, k: int) -> str:
        return solve(s, k)
