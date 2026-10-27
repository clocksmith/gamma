"""Original candidate for LeetCode 3137. Contract: https://leetcode.com/problems/minimum-number-of-operations-to-make-word-k-periodic/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n) expected time and space"""
from collections import Counter

def solve(word,k):
    counts=Counter(word[i:i+k] for i in range(0,len(word),k))
    return len(word)//k-max(counts.values())
