# Original implementation. Contract: https://leetcode.com/problems/substrings-that-begin-and-end-with-the-same-letter/
from collections import Counter
def solve(s):return sum(x*(x+1)//2 for x in Counter(s).values())
