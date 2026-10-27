"""558. Logical OR of Two Binary Grids Represented as Quad-Trees. Build an independent compressed result; neither input tree is modified or aliased."""

class Node:
    def __init__(self, val=False, isLeaf=False, topLeft=None, topRight=None,
                 bottomLeft=None, bottomRight=None):
        self.val = val
        self.isLeaf = isLeaf
        self.topLeft = topLeft
        self.topRight = topRight
        self.bottomLeft = bottomLeft
        self.bottomRight = bottomRight

def solve(quadTree1, quadTree2):
    def copy(node):
        if node.isLeaf:
            return Node(bool(node.val), True)
        return Node(False, False, copy(node.topLeft), copy(node.topRight),
                    copy(node.bottomLeft), copy(node.bottomRight))
    def merge(a, b):
        if a.isLeaf:
            return Node(True, True) if a.val else copy(b)
        if b.isLeaf:
            return Node(True, True) if b.val else copy(a)
        children = [merge(a.topLeft, b.topLeft), merge(a.topRight, b.topRight),
                    merge(a.bottomLeft, b.bottomLeft), merge(a.bottomRight, b.bottomRight)]
        if all(child.isLeaf and child.val == children[0].val for child in children):
            return Node(children[0].val, True)
        return Node(False, False, *children)
    return merge(quadTree1, quadTree2)


class Solution:
    def intersect(self, quadTree1, quadTree2):
        return solve(quadTree1, quadTree2)
