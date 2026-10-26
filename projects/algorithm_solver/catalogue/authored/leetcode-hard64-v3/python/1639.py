"""1639. Number of Ways to Form a Target String Given a Dictionary: column counts and backward target DP; O(columns*(words+target length)) time and O(target length) space."""


def solve(words: list[str], target: str) -> int:
    modulus = 1_000_000_007
    ways = [0] * (len(target) + 1)
    ways[0] = 1
    for column in range(len(words[0])):
        frequency = [0] * 26
        for word in words:
            frequency[ord(word[column]) - ord('a')] += 1
        for length in range(min(len(target), column + 1), 0, -1):
            count = frequency[ord(target[length - 1]) - ord('a')]
            ways[length] = (ways[length] + ways[length - 1] * count) % modulus
    return ways[-1]


class Solution:
    def numWays(self, words: list[str], target: str) -> int:
        return solve(words, target)
