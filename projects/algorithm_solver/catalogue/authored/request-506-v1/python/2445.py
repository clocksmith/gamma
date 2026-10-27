"""Original candidate for LeetCode 2445. Contract: https://leetcode.com/problems/number-of-nodes-with-value-one/
Definition additionally checked against public doocs/leetcode documentation (CC-BY-SA-4.0); original implementation.
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n+q) time, O(n) space"""
def solve(n,queries):
    flips=[0]*(n+1)
    for q in queries:flips[q]^=1
    for i in range(1,n+1):flips[i]^=flips[i//2]
    return sum(flips)
