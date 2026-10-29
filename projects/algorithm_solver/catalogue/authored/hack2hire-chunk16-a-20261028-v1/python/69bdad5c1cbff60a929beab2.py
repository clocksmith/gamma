"""Hack2Hire 69bdad5c1cbff60a929beab2 (Maximum Profit Query Selection) over an INFERRED spec; qualification unknown."""


def solve(executionTime, profit, k):
    best, index = 0, -1
    for i in range(len(executionTime)):
        value = (k // executionTime[i]) * profit[i]
        if value > best:
            best, index = value, i
    return [best, index]


class Solution:
    def maxProfitQuery(self, executionTime, profit, k):
        return solve(executionTime, profit, k)
