class Solution:
    def numDistinct(self, s: str, t: str) -> int:
        counts = [0] * (len(t) + 1)
        counts[0] = 1
        for character in s:
            for index in range(len(t) - 1, -1, -1):
                if character == t[index]:
                    counts[index + 1] += counts[index]
        return counts[-1]
