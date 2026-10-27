# Original implementation. Contract: https://leetcode.com/problems/number-of-employees-who-met-the-target/
def solve(hours,target):return sum(x>=target for x in hours)
