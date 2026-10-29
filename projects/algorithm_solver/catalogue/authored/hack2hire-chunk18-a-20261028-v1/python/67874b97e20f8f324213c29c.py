"""Hack2Hire 67874b97e20f8f324213c29c (Maximum Number of Balanced Shipments) over an INFERRED spec; qualification unknown."""


def solve(weights):
    n = len(weights)
    best = [-1] * (n + 1)
    best[0] = 0
    prefix = [0] * (n + 1)
    stack = []
    for i in range(n):
        while stack and weights[stack[-1]] <= weights[i]:
            stack.pop()
        if stack and prefix[stack[-1]] >= 0:
            best[i + 1] = prefix[stack[-1]] + 1
        stack.append(i)
        prefix[i + 1] = max(prefix[i], best[i + 1])
    return max(best[n], 0)


class Solution:
    def maxBalancedShipments(self, weights):
        return solve(weights)
