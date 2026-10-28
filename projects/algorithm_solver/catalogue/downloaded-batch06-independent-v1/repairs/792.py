"""792. New separately tracked functional variant: advance only waiting words."""
from collections import Counter


def solve(s: str, words: list[str]) -> int:
    waiting = [[] for _ in range(26)]
    for word, multiplicity in Counter(words).items():
        waiting[ord(word[0]) - 97].append((word, 1, multiplicity))
    answer = 0
    for char in s:
        index = ord(char) - 97
        ready = waiting[index]
        waiting[index] = []
        for word, position, multiplicity in ready:
            if position == len(word):
                answer += multiplicity
            else:
                waiting[ord(word[position]) - 97].append((word, position + 1, multiplicity))
    return answer


class Solution:
    def numMatchingSubseq(self, s: str, words: list[str]) -> int:
        return solve(s, words)
