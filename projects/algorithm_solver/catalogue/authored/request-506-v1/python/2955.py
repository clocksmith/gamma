# Original candidate. Contract: https://leetcode.com/problems/number-of-same-end-substrings/
def solve(s, queries):
    prefix=[[0]*(len(s)+1) for _ in range(26)]
    for c in range(26):
        for i,x in enumerate(s):prefix[c][i+1]=prefix[c][i]+(ord(x)-97==c)
    return [sum((row[r+1]-row[l])*(row[r+1]-row[l]+1)//2 for row in prefix) for l,r in queries]
