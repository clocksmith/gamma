class Solution:
    def longestCommonSubsequence(self, text1: str, text2: str) -> int:
        if not text1 or not text2:
            return 0
        if len(text1) < len(text2):
            text1, text2 = text2, text1
        lengths = [0] * (len(text2) + 1)
        for first in text1:
            diagonal = 0
            for index, second in enumerate(text2, 1):
                above = lengths[index]
                if first == second:
                    lengths[index] = diagonal + 1
                else:
                    lengths[index] = max(lengths[index], lengths[index - 1])
                diagonal = above
        return lengths[-1]
