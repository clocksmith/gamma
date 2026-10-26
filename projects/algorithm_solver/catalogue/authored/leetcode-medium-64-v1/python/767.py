"""767. Reorganize String: fill alternating positions in descending frequency order."""


def solve(s: str) -> str:
    """O(n + a log a) time and O(n + a) space for a <= 26 distinct letters; inputs are read-only."""
    counts = [0] * 26
    for character in s:
        counts[ord(character) - ord('a')] += 1
    if max(counts) > (len(s) + 1) // 2:
        return ''
    letters = sorted(range(26), key=lambda letter: (-counts[letter], letter))
    answer = [''] * len(s)
    position = 0
    for letter in letters:
        for _ in range(counts[letter]):
            if position >= len(s):
                position = 1
            answer[position] = chr(ord('a') + letter)
            position += 2
    return ''.join(answer)


class Solution:
    def reorganizeString(self, s: str) -> str:
        return solve(s)
