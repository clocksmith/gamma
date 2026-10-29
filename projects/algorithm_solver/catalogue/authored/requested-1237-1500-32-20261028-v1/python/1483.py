"""Original frontend 1483 variant; qualification unknown."""


class TreeAncestor:
    def __init__(self, n: int, parent):
        max_log = 16
        up = [list(parent)]
        for _ in range(1, max_log):
            prev = up[-1]
            nxt = [-1 if p == -1 else prev[p] for p in prev]
            up.append(nxt)
        self.up = up

    def getKthAncestor(self, node: int, k: int) -> int:
        curr = node
        bit = 0
        while k > 0 and curr != -1:
            if k & 1:
                curr = self.up[bit][curr]
            k >>= 1
            bit += 1
        return curr


def solve(operation_names, argument_lists):
    n, parent = argument_lists[0]
    inst = TreeAncestor(n, parent)
    out = [None]
    for op, args in zip(operation_names[1:], argument_lists[1:]):
        out.append(inst.getKthAncestor(args[0], args[1]))
    return out
