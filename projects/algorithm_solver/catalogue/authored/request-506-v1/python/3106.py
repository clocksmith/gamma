# Original implementation. Contract: https://leetcode.com/problems/lexicographically-smallest-string-after-operations-with-constraint/
def solve(s,k):
    out=[]
    for c in s:
        x=ord(c)-97;cost=min(x,26-x)
        if cost<=k:out.append('a');k-=cost
        else:out.append(chr(97+x-k));k=0
    return ''.join(out)
