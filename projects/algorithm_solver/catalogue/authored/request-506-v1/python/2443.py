# Original candidate. Contract: https://leetcode.com/problems/sum-of-number-and-its-reverse/
def solve(num):
    return any(x+int(str(x)[::-1])==num for x in range(num+1))
