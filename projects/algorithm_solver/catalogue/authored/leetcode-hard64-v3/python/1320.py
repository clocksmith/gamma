"""1320. Minimum Distance to Type a Word Using Two Fingers: DP over the idle finger and last typed key; O(26*n) time and O(26) space."""


def solve(word: str) -> int:
    def distance(first: int, second: int) -> int:
        if first == 26:
            return 0
        return abs(first // 6 - second // 6) + abs(first % 6 - second % 6)

    best = [float('inf')] * 27
    best[26] = 0
    previous = 26
    for character in word:
        current = ord(character) - ord('A')
        following = [float('inf')] * 27
        for idle, cost in enumerate(best):
            following[idle] = min(following[idle], cost + distance(previous, current))
            following[previous] = min(following[previous], cost + distance(idle, current))
        best = following
        previous = current
    return min(best)


class Solution:
    def minimumDistance(self, word: str) -> int:
        return solve(word)
