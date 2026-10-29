"""Hack2Hire 67d8a1d71989183df538251a (Maximize Server Throughput) over an INFERRED spec; qualification unknown."""


def solve(hostThroughput):
    values = sorted(hostThroughput, reverse=True)
    total = 0
    for i in range(len(values) // 3):
        total += values[2 * i + 1]
    return total


class Solution:
    def maximizeThroughput(self, hostThroughput):
        return solve(hostThroughput)
