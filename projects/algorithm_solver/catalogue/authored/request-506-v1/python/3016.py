# Original implementation. Contract: https://leetcode.com/problems/minimum-number-of-pushes-to-type-word-ii/
from collections import Counter
def solve(word):return sum(c*(i//8+1) for i,c in enumerate(sorted(Counter(word).values(),reverse=True)))
