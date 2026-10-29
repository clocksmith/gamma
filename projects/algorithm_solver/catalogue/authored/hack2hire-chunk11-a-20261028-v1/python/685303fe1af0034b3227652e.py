"""Hack2Hire 685303fe1af0034b3227652e (Find Path in Fibonacci Tree) over an INFERRED spec; qualification unknown."""


def solve(n, startValue, destValue):
    size = [0, 1]  # S(0) = 0, S(1) = 1, S(m) = 1 + S(m - 2) + S(m - 1)
    for m in range(2, n + 1):
        size.append(1 + size[m - 2] + size[m - 1])

    def steps(label):
        out, order = [], n
        while label:
            label -= 1  # skip the current root in pre-order
            if label < size[order - 2]:
                out.append('L')
                order -= 2
            else:
                label -= size[order - 2]
                out.append('R')
                order -= 1
        return out

    a, b = steps(startValue), steps(destValue)
    i = 0
    while i < len(a) and i < len(b) and a[i] == b[i]:
        i += 1
    return 'U' * (len(a) - i) + ''.join(b[i:])


class Solution:
    def findPath(self, n, startValue, destValue):
        return solve(n, startValue, destValue)
