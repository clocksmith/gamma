# Original candidate. Contract: https://leetcode.com/problems/maximum-number-that-makes-result-of-bitwise-and-zero/
def solve(n):
    return (1<<(n.bit_length()-1))-1
