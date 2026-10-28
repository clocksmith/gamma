from collections import Counter
from functools import lru_cache


class Solution:
    def isScramble(self, s1, s2):
        @lru_cache(None)
        def match(i, j, length):
            left, right = s1[i:i + length], s2[j:j + length]
            if left == right:
                return True
            if Counter(left) != Counter(right):
                return False
            for split in range(1, length):
                if match(i, j, split) and match(i + split, j + split, length - split):
                    return True
                if match(i, j + length - split, split) and match(i + split, j, length - split):
                    return True
            return False
        return match(0, 0, len(s1))
