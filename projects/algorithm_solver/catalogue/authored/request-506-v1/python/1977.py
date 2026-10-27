# Original implementation. Contract: https://leetcode.com/problems/number-of-ways-to-separate-numbers/
from array import array
def solve(num):
    n=len(num);mod=1000000007
    lcp=[array('H',[0])*(n+1) for _ in range(n+1)]
    for i in range(n-1,-1,-1):
        for j in range(i+1,n):
            if num[i]==num[j]:lcp[i][j]=lcp[i+1][j+1]+1
    dp=[array('I',[0])*(i+1) for i in range(n+1)]
    for end in range(1,n+1):
        for length in range(1,end+1):
            start=end-length;ways=0
            if num[start]!='0':
                if start==0:ways=1
                else:
                    ways=dp[start][min(start,length-1)]
                    if length<=start:
                        previous=start-length;equal=lcp[previous][start]
                        if equal>=length or num[previous+equal]<=num[start+equal]:ways+=dp[start][length]-dp[start][length-1]
            dp[end][length]=(dp[end][length-1]+ways)%mod
    return dp[n][n]
