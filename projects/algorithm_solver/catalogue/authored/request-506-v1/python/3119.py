"""Original candidate for LeetCode 3119. Contract: https://leetcode.com/problems/maximum-number-of-potholes-that-can-be-fixed/
Definition additionally checked against public doocs/leetcode documentation (CC-BY-SA-4.0); original implementation.
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n log n) time, O(n) space"""
def solve(road,budget):
    runs=sorted((len(s) for s in road.split('.') if s),reverse=True);ans=0
    for run in runs:
        take=min(run,max(0,budget-1));ans+=take;budget-=take+1
        if budget<=1:break
    return ans
