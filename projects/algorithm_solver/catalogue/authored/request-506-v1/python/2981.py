# Original candidate implementation. Contract: https://leetcode.com/problems/find-longest-special-substring-that-occurs-thrice-i/
def solve(s):
    counts={}; answer=-1
    for i in range(len(s)):
        for j in range(i,len(s)):
            if s[j]!=s[i]: break
            key=(s[i],j-i+1); counts[key]=counts.get(key,0)+1
            if counts[key]>=3: answer=max(answer,j-i+1)
    return answer
