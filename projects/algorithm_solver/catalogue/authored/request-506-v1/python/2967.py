# Original candidate. Contract: https://leetcode.com/problems/minimum-cost-to-make-array-equalindromic/
def solve(nums):
    a=sorted(nums);m=a[len(a)//2];s=str(m);L=len(s);prefix=int(s[:(L+1)//2]);candidates={10**(L-1)-1,10**L+1}
    for p in range(max(0,prefix-1),prefix+2):
        t=str(p);candidates.add(int(t+(t[:-1] if L%2 else t)[::-1]))
    return min(sum(abs(x-p) for x in a) for p in candidates if 0<p<10**9)
