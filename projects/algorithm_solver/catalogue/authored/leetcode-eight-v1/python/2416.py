"""Count prefix visits in a compact trie with a fixed lowercase alphabet."""
from array import array


def solve(words: list[str]) -> list[int]:
    """O(S) time/space for total length S; at most 26 siblings per trie node."""
    capacity = 1 + sum(map(len, words))
    first = array("i", [-1]) * capacity
    sibling = array("i", [-1]) * capacity
    counts = array("I", [0]) * capacity
    letters = bytearray(capacity)
    used = 1
    for word in words:
        node = 0
        for letter in word:
            code = ord(letter) - ord("a")
            child = first[node]
            while child != -1 and letters[child] != code:
                child = sibling[child]
            if child == -1:
                child = used
                used += 1
                letters[child] = code
                sibling[child] = first[node]
                first[node] = child
            counts[child] += 1
            node = child
    result = []
    for word in words:
        node = score = 0
        for letter in word:
            code = ord(letter) - ord("a")
            child = first[node]
            while letters[child] != code:
                child = sibling[child]
            score += counts[child]
            node = child
        result.append(score)
    return result


class Solution:
    def sumPrefixScores(self, words: list[str]) -> list[int]:
        return solve(words)
