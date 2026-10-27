"""Original candidate for LeetCode 2647. Contract: https://leetcode.com/problems/color-the-triangle-red/
Definition additionally checked against public doocs/leetcode documentation (CC-BY-SA-4.0); original implementation.
Development tests only; not admitted or independently qualified.
Returns [row,position] seeds, rows1..n and positions1..2row-1. Original four-row fringe construction; see independent construction note and infection tests. Ordering is noncanonical and immaterial.
Complexity: O(n²) time/output space"""
def solve(n):
    out=[]
    while n>=4:
        out.extend([n,c] for c in range(1,2*n,2));out.append([n-1,2*n-4])
        for r in (n-2,n-3):
            for c in range(1,2*r,4):out.append([r,c-1 if n%2 and r==n-2 and c==2*n-5 else c])
        n-=4
    if n>=1:out.append([1,1])
    if n>=2:out.extend([[2,1],[2,3]])
    if n==3:out.extend([[3,1],[3,5]])
    return out
