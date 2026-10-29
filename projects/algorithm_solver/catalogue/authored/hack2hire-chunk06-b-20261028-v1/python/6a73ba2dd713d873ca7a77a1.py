"""Hack2Hire 6a73ba2dd713d873ca7a77a1 (Largest Number by Parity Swaps) over an INFERRED spec; qualification unknown."""

def solve(num):
    out, i, n = [], 0, len(num)
    while i < n:
        parity = ord(num[i]) & 1
        count = [0] * 10
        j = i
        while j < n and (ord(num[j]) & 1) == parity:
            count[ord(num[j]) - 48] += 1
            j += 1
        for d in range(9, -1, -1):
            if count[d]:
                out.append(str(d) * count[d])
        i = j
    return ''.join(out)


class Solution:
    def largestByParitySwaps(self, num):
        return solve(num)
