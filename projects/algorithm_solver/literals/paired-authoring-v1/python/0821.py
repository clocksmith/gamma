class Solution:
    def shortestToChar(self, s: str, c: str) -> list[int]:
        distances = [0] * len(s)
        previous = -len(s)
        for index, character in enumerate(s):
            if character == c:
                previous = index
            distances[index] = index - previous
        following = 2 * len(s)
        for index in range(len(s) - 1, -1, -1):
            if s[index] == c:
                following = index
            distances[index] = min(distances[index], following - index)
        return distances
