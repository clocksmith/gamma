# Original candidate. Contract: https://leetcode.com/problems/find-the-index-of-permutation/
def solve(perm):
    n=len(perm);mod=1000000007;fact=[1]*(n+1);bit=[i&-i for i in range(n+1)]
    for i in range(1,n+1):fact[i]=fact[i-1]*i%mod
    answer=0
    for i,x in enumerate(perm):
        j=x-1;smaller=0
        while j:smaller+=bit[j];j-=j&-j
        answer=(answer+smaller*fact[n-i-1])%mod;j=x
        while j<=n:bit[j]-=1;j+=j&-j
    return answer
