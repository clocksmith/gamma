# Original candidate. Contract: https://leetcode.com/problems/minimum-cost-to-separate-sentence-into-rows/
def solve(sentence, k):
    words=sentence.split();n=len(words);dp=[float('inf')]*(n+1);dp[n]=0
    for i in range(n-1,-1,-1):
        length=-1
        for j in range(i,n):
            length+=1+len(words[j])
            if length>k:break
            dp[i]=min(dp[i],(k-length)**2+dp[j+1] if j<n-1 else 0)
    return dp[0]
