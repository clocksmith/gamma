"""Original candidate for LeetCode 3180. Contract: https://leetcode.com/problems/maximum-total-reward-using-operations-i/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n log n + n*M/word_size) time, O(M) bits; M=max reward"""
def solve(rewardValues):
    bits=1
    for x in sorted(set(rewardValues)):bits|=(bits&((1<<x)-1))<<x
    return bits.bit_length()-1
