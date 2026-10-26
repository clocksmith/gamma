"""1297. Maximum Number of Occurrences of a Substring: count valid minimum-length windows since extending a substring cannot increase its frequency."""


def solve(s: str, maxLetters: int, minSize: int, maxSize: int) -> int:
    """O(n * minSize) time and O(n * minSize) auxiliary space including substring keys; inputs are read-only."""
    counts = [0] * 26
    distinct = best = 0
    frequency = {}
    for right, letter in enumerate(s):
        index = ord(letter) - ord('a')
        if counts[index] == 0:
            distinct += 1
        counts[index] += 1
        if right >= minSize:
            outgoing = ord(s[right - minSize]) - ord('a')
            counts[outgoing] -= 1
            if counts[outgoing] == 0:
                distinct -= 1
        if right + 1 >= minSize and distinct <= maxLetters:
            word = s[right - minSize + 1:right + 1]
            frequency[word] = frequency.get(word, 0) + 1
            best = max(best, frequency[word])
    return best


class Solution:
    def maxFreq(self, s: str, maxLetters: int, minSize: int, maxSize: int) -> int:
        return solve(s, maxLetters, minSize, maxSize)
