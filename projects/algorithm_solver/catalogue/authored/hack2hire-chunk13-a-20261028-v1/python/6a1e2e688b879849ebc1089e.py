"""Hack2Hire 6a1e2e688b879849ebc1089e (Obstacle Placement and Block Check) over an INFERRED spec; qualification unknown."""
from bisect import bisect_left


def solve(operations):
    coords = sorted({op[1] for op in operations if op[0] == 1})
    m = len(coords)
    tree = [0] * (m + 1)  # Fenwick tree of placed obstacles over the compressed positions
    placed = [False] * m

    def prefix(i):  # obstacles among the first i compressed positions
        total = 0
        while i > 0:
            total += tree[i]
            i -= i & -i
        return total

    out = []
    for op in operations:
        if op[0] == 1:
            k = bisect_left(coords, op[1])
            if not placed[k]:
                placed[k] = True
                k += 1
                while k <= m:
                    tree[k] += 1
                    k += k & -k
        else:
            x, size = op[1], op[2]
            inside = prefix(bisect_left(coords, x)) - prefix(bisect_left(coords, x - size))
            out.append('1' if inside == 0 else '0')
    return ''.join(out)


class Solution:
    def processOperations(self, operations):
        return solve(operations)
