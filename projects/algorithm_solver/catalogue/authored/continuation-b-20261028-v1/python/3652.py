def solve(prices, strategy, k):
    original = [0]
    values = [0]
    for p, s in zip(prices, strategy):
        original.append(original[-1]+p*s)
        values.append(values[-1]+p)
    gain = 0
    for start in range(len(prices)-k+1):
        gain = max(gain, -(original[start+k]-original[start]) + values[start+k]-values[start+k//2])
    return original[-1]+gain

class Solution:
    def maxProfit(self, prices, strategy, k):
        return solve(prices, strategy, k)
