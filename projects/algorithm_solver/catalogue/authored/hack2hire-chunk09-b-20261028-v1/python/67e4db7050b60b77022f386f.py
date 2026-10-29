"""Hack2Hire 67e4db7050b60b77022f386f (Compress N-ary Tree) over an INFERRED spec; qualification unknown."""


def solve(tree, compressedNodes):
    root = tree[0][0]
    gone = set(compressedNodes)
    gone.discard(root)
    parent = {}
    for value, children in tree:
        for child in children:
            parent[child] = value
    kept_ancestor = {}
    new_children = {root: []}
    order = [root]
    for value, _ in tree[1:]:
        p = parent[value]
        anchor = p if p not in gone else kept_ancestor[p]
        kept_ancestor[value] = anchor
        if value not in gone:
            new_children[anchor].append(value)
            new_children[value] = []
            order.append(value)
    return [[value, new_children[value]] for value in order]


class Solution:
    def compressTree(self, tree, compressedNodes):
        return solve(tree, compressedNodes)
