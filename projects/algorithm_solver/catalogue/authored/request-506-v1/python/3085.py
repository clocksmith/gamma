# Original implementation. Contract: https://leetcode.com/problems/minimum-deletions-to-make-string-k-special/
from collections import Counter
def solve(word,k):
    counts=list(Counter(word).values())
    return min(sum(x if x<low else max(0,x-low-k) for x in counts) for low in counts)
