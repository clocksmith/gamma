"""Original candidate for LeetCode 2080. Contract: https://leetcode.com/problems/range-frequency-queries/
Development tests only; not admitted or independently qualified.
Batch adapter solve(operations, arguments) follows RangeFreqQuery class-call arrays.
Complexity: O(n) initialization, O(log n) per query, O(n+q) space"""
from bisect import bisect_left,bisect_right

def solve(operations,arguments):
    positions={}
    for i,x in enumerate(arguments[0][0]):positions.setdefault(x,[]).append(i)
    out=[None]
    for left,right,value in arguments[1:]:
        a=positions.get(value,[]);out.append(bisect_right(a,right)-bisect_left(a,left))
    return out
