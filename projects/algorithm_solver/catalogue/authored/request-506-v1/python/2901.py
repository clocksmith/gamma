# Original candidate implementation. Contract: https://leetcode.com/problems/longest-unequal-adjacent-groups-subsequence-ii/
def solve(words,groups):
    n=len(words);dp=[1]*n;previous=[-1]*n
    for i in range(n):
        for j in range(i):
            if groups[i]!=groups[j] and len(words[i])==len(words[j]) and sum(a!=b for a,b in zip(words[i],words[j]))==1 and dp[j]+1>dp[i]:dp[i]=dp[j]+1;previous[i]=j
    current=max(range(n),key=lambda i:dp[i]);out=[]
    while current>=0:out.append(words[current]);current=previous[current]
    return out[::-1]
