# Original candidate implementation. Contract: https://leetcode.com/problems/range-product-queries-of-powers/
def solve(n,queries):
    prefix=[0]
    for bit in range(n.bit_length()):
        if n>>bit&1:prefix.append(prefix[-1]+bit)
    mod=1000000007;powers=[1]
    for _ in range(prefix[-1]):powers.append(powers[-1]*2%mod)
    return [powers[prefix[r+1]-prefix[l]] for l,r in queries]
