"""Hack2Hire 678876fe402dc47b67a14944 (Array Generation Service) over an INFERRED spec; qualification unknown."""


def solve(arr, state, m):
    bucket = [0] * m  # bucket[d]: largest value that becomes available before operation d + 1
    last = -1
    for i in range(len(arr)):
        if state[i] == '1':
            last = i
        if last >= 0:
            d = i - last
            if d < m and arr[i] > bucket[d]:
                bucket[d] = arr[i]
    result = []
    current = 0
    for t in range(m):
        if bucket[t] > current:
            current = bucket[t]
        result.append(current)
    return result


class Solution:
    def getMaximumArray(self, arr, state, m):
        return solve(arr, state, m)
