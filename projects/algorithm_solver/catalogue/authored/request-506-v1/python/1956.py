"""Original candidate for LeetCode 1956. Contract: https://leetcode.com/problems/minimum-time-for-k-virus-variants-to-spread/
Definition additionally checked against public doocs/leetcode documentation (CC-BY-SA-4.0); original implementation.
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(A n log n) time, O(n) space; A <= 10000 candidate lattice centers"""
def solve(points,k):
    return min(sorted(abs(x-a)+abs(y-b) for a,b in points)[k-1] for x in range(min(p[0] for p in points),max(p[0] for p in points)+1) for y in range(min(p[1] for p in points),max(p[1] for p in points)+1))
