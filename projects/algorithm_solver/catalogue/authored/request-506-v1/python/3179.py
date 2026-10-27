# Original candidate. Contract: https://leetcode.com/problems/find-the-n-th-value-after-k-seconds/
def solve(n, k):
    a=[1]*n
    for _ in range(k):
        for i in range(1,n):a[i]=(a[i]+a[i-1])%1000000007
    return a[-1]
