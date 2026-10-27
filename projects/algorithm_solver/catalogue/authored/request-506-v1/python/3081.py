"""Original candidate for LeetCode 3081. Contract: https://leetcode.com/problems/replace-question-marks-in-string-to-minimize-its-value/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n log n) time, O(n) space"""
def solve(s):
    counts=[0]*26
    for c in s:
        if c!='?':counts[ord(c)-97]+=1
    added=[]
    for _ in range(s.count('?')):
        j=min(range(26),key=lambda j:counts[j]);counts[j]+=1;added.append(chr(j+97))
    added.sort();it=iter(added)
    return ''.join(next(it) if c=='?' else c for c in s)
