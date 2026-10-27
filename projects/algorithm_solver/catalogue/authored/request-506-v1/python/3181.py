# Original implementation. Contract: https://leetcode.com/problems/maximum-total-reward-using-operations-ii/
def solve(rewardValues):
    bits=1
    for x in sorted(set(rewardValues)):bits|=(bits&((1<<x)-1))<<x
    return bits.bit_length()-1
