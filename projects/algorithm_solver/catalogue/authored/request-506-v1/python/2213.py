"""Original candidate for LeetCode 2213. Contract: https://leetcode.com/problems/longest-substring-of-one-repeating-character/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n+q log n) time, O(n+q) space"""
def solve(s,queryCharacters,queryIndices):
    chars=list(s);n=len(s);prefix=[0]*(4*n);suffix=[0]*(4*n);best=[0]*(4*n)
    def pull(v,l,r):
        m=(l+r)//2;a=v*2;b=a+1;prefix[v]=prefix[a];suffix[v]=suffix[b];best[v]=max(best[a],best[b])
        if chars[m]==chars[m+1]:
            best[v]=max(best[v],suffix[a]+prefix[b])
            if prefix[a]==m-l+1:prefix[v]+=prefix[b]
            if suffix[b]==r-m:suffix[v]+=suffix[a]
    def build(v,l,r):
        if l==r:prefix[v]=suffix[v]=best[v]=1;return
        m=(l+r)//2;build(v*2,l,m);build(v*2+1,m+1,r);pull(v,l,r)
    def update(v,l,r,i):
        if l==r:return
        m=(l+r)//2
        if i<=m:update(v*2,l,m,i)
        else:update(v*2+1,m+1,r,i)
        pull(v,l,r)
    build(1,0,n-1);out=[]
    for c,i in zip(queryCharacters,queryIndices):chars[i]=c;update(1,0,n-1,i);out.append(best[1])
    return out
