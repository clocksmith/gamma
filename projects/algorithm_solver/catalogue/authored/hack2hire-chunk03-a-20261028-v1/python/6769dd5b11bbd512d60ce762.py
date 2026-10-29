"""Hack2Hire 6769dd5b11bbd512d60ce762 (Max Sum Between Leaf Nodes) over an INFERRED spec; qualification unknown."""


def solve(tree):
    vals, left, right = [tree[0]], [-1], [-1]
    queue_head, i = 0, 1
    while i < len(tree):
        parent = queue_head
        queue_head += 1
        for side in (left, right):
            if i < len(tree):
                if tree[i] is not None:
                    vals.append(tree[i])
                    left.append(-1)
                    right.append(-1)
                    side[parent] = len(vals) - 1
                i += 1
    n = len(vals)
    down = [0] * n
    best = None
    leaves, leaf_value = 0, 0
    for v in range(n - 1, -1, -1):  # children always have larger level-order indices
        l, r = left[v], right[v]
        if l < 0 and r < 0:
            down[v] = vals[v]
            leaves += 1
            leaf_value = vals[v]
        elif l < 0 or r < 0:
            down[v] = vals[v] + down[l if l >= 0 else r]
        else:
            down[v] = vals[v] + max(down[l], down[r])
            through = down[l] + down[r] + vals[v]
            if best is None or through > best:
                best = through
    return leaf_value if leaves == 1 else best


class Solution:
    def maxLeafToLeafSum(self, tree):
        return solve(tree)
