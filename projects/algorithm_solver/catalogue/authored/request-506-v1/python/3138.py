# Original implementation. Contract: https://leetcode.com/problems/minimum-length-of-anagram-concatenation/
from collections import Counter
def solve(s):
    n=len(s)
    for size in range(1,n+1):
        if n%size==0:
            c=Counter(s[:size])
            if all(Counter(s[i:i+size])==c for i in range(size,n,size)):return size
