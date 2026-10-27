# Original implementation. Contract: https://leetcode.com/problems/apply-operations-to-make-string-empty/
from collections import Counter
def solve(s):
    counts=Counter(s);maximum=max(counts.values());last={c:i for i,c in enumerate(s)}
    return ''.join(c for i,c in enumerate(s) if counts[c]==maximum and last[c]==i)
