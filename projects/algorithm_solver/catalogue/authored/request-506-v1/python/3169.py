"""Original candidate for LeetCode 3169. Contract: https://leetcode.com/problems/count-days-without-meetings/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n log n) time, O(n) space"""
def solve(days,meetings):
    end=0;busy=0
    for left,right in sorted(meetings):
        if right>end:busy+=right-max(end,left-1);end=right
    return days-busy
