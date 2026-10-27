"""Original candidate for LeetCode 2844. Contract: https://leetcode.com/problems/minimum-operations-to-make-a-special-number/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n) time; O(1) Python, O(n) JS temporary space"""
def solve(num):
    n=len(num);ans=n-('0' in num)
    for end in ('00','25','50','75'):
        j=num.rfind(end[1])
        if j>=0:
            i=num.rfind(end[0],0,j)
            if i>=0:ans=min(ans,n-i-2)
    return ans
