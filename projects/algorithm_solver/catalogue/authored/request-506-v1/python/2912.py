# Original implementation. Contract: https://leetcode.com/problems/number-of-ways-to-reach-destination-in-the-grid/
def solve(n,m,k,source,dest):
    mod=1000000007;state=[0]*4
    same_row=source[0]==dest[0];same_col=source[1]==dest[1]
    state[0 if same_row and same_col else 1 if same_row else 2 if same_col else 3]=1
    for _ in range(k):
        a,b,c,d=state
        state=[(b+c)%mod,((m-1)*a+(m-2)*b+d)%mod,((n-1)*a+(n-2)*c+d)%mod,((n-1)*b+(m-1)*c+(n+m-4)*d)%mod]
    return state[0]
